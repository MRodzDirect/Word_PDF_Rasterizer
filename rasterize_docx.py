#!/usr/bin/env python3
"""
rasterize_docx.py

Turn source .docx (or .pdf) into a NEW .docx and .pdf that contain ONLY
full-page images, in original page order, with zero live/editable text.

Pipeline (all local, no OCR anywhere):
  1. source .docx  --[LibreOffice headless]-->  source.pdf   (pure render)
     (skip this step if source is already a .pdf)
  2. source.pdf    --[pdftoppm, poppler-utils]--> page_001.png, page_002.png...
     high-DPI raster, one image per page, page order = filename order
  3. page_*.png    --[python-docx]--> output.docx   (one InlineShape image
     per page, full page width, page break between, zero paragraphs of text)
  4. page_*.png    --[img2pdf]--> output.pdf   (lossless image embed,
     no re-encode, no text layer -- img2pdf never runs OCR)

Why this route and not Word copy/paste:
  Word's clipboard does not carry a "one image per source page" concept.
  Multi-page copy from a doc/PDF viewer collapses into a single blob (often
  still carrying a live text layer). Rasterizing outside Word and inserting
  each page as a discrete embedded picture is the only way to GUARANTEE
  page-for-page image fidelity with no editable text.

Usage:
  python3 rasterize_docx.py SOURCE.docx [--dpi 300] [--out-prefix output]
  python3 rasterize_docx.py SOURCE.pdf  [--dpi 300] [--out-prefix output]

Outputs (in same dir unless --out-dir given):
  <out-prefix>.docx   -- image-only Word doc
  <out-prefix>.pdf    -- image-only PDF
  <out-prefix>_pages/ -- the raw page PNGs (kept for inspection/reuse)

Requires: soffice (LibreOffice), pdftoppm (poppler-utils),
          python-docx, img2pdf, Pillow  -- all already present in this env.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.section import WD_SECTION
from PIL import Image
import img2pdf

# soffice.py wrapper shipped with the docx skill -- calls real `soffice`
# headless and is the same converter Word-doc verification uses elsewhere
# in this environment. Falls back to calling `soffice` directly if that
# wrapper isn't present (e.g. script copied outside this environment).
SOFFICE_WRAPPER = Path("/mnt/skills/public/docx/scripts/office/soffice.py")

# Set this if `soffice` isn't on PATH (e.g. portable install on Windows).
# Leave as None to just use "soffice" from PATH.
SOFFICE_EXE = r"C:\Users\MRodz\Desktop\All Programs\Basic-Ware\LibreOfficePortable\App\libreoffice\program\soffice.exe"


def log(msg: str) -> None:
    print(f"[rasterize] {msg}", flush=True)


def run(cmd: list, **kwargs) -> subprocess.CompletedProcess:
    log("$ " + " ".join(str(c) for c in cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        log(f"STDOUT: {result.stdout}")
        log(f"STDERR: {result.stderr}")
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(str(c) for c in cmd)}")
    return result


def docx_to_pdf(source_docx: Path, workdir: Path) -> Path:
    """Pure LibreOffice render, docx -> pdf. No OCR, no text extraction --
    this is a print-to-PDF style conversion, source text stays as vector
    text inside that intermediate PDF (irrelevant, since we rasterize next
    and throw the intermediate PDF away)."""
    log(f"Converting {source_docx.name} to PDF via LibreOffice (headless)...")
    if SOFFICE_WRAPPER.exists():
        cmd = ["python3", str(SOFFICE_WRAPPER), "--headless", "--convert-to", "pdf",
               "--outdir", str(workdir), str(source_docx)]
    elif shutil.which("soffice"):
        cmd = ["soffice", "--headless", "--convert-to", "pdf",
               "--outdir", str(workdir), str(source_docx)]
    else:
        cmd = [SOFFICE_EXE, "--headless", "--convert-to", "pdf",
               "--outdir", str(workdir), str(source_docx)]
    run(cmd)
    produced = workdir / (source_docx.stem + ".pdf")
    if not produced.exists():
        raise RuntimeError(f"Expected {produced} after LibreOffice conversion, not found")
    return produced


def pdf_to_page_images(pdf_path: Path, pages_dir: Path, dpi: int) -> list:
    """Rasterize every page to a PNG. pdftoppm guarantees page order via
    zero-padded sequential filenames -- no OCR, no text layer involved,
    this is a pure pixel render of each page."""
    pages_dir.mkdir(parents=True, exist_ok=True)
    log(f"Rasterizing {pdf_path.name} at {dpi} DPI...")
    prefix = pages_dir / "page"
    run(["pdftoppm", "-png", "-r", str(dpi), str(pdf_path), str(prefix)])
    images = sorted(pages_dir.glob("page-*.png"))
    if not images:
        raise RuntimeError("pdftoppm produced no page images")
    log(f"Got {len(images)} page images.")
    return images


def build_image_only_docx(images: list, out_path: Path, dpi: int) -> None:
    """One embedded picture per page, full page width, page break between.
    Section page size is set per-image to match that image's own aspect
    ratio, so mixed portrait/landscape/letter/A4 source pages don't stretch
    or letterbox. Zero text runs are added anywhere in the document."""
    doc = Document()

    # Some default templates ship a single empty paragraph; remove it so
    # the first page break doesn't leave a blank leading page. Guarded
    # because not all templates include it.
    if doc.paragraphs:
        first_para = doc.paragraphs[0]
        first_para._element.getparent().remove(first_para._element)

    for i, img_path in enumerate(images):
        with Image.open(img_path) as im:
            px_w, px_h = im.size
        # px -> inches using the DPI we rasterized at, so page size in the
        # docx exactly matches the source page's physical dimensions.
        width_in = px_w / dpi
        height_in = px_h / dpi

        if i == 0:
            section = doc.sections[0]
        else:
            section = doc.add_section(WD_SECTION.NEW_PAGE)

        section.page_width = Inches(width_in)
        section.page_height = Inches(height_in)
        section.top_margin = Pt(0)
        section.bottom_margin = Pt(0)
        section.left_margin = Pt(0)
        section.right_margin = Pt(0)

        para = doc.add_paragraph()
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(0)
        run_ = para.add_run()
        run_.add_picture(str(img_path), width=Inches(width_in), height=Inches(height_in))

    doc.save(str(out_path))
    log(f"Wrote {out_path}")


def build_image_only_pdf(images: list, out_path: Path) -> None:
    """img2pdf embeds the original image bytes losslessly (no re-encode,
    no re-compression, no OCR pass) -- output PDF pages are pure raster
    images, zero text layer."""
    with open(out_path, "wb") as f:
        f.write(img2pdf.convert([str(p) for p in images]))
    log(f"Wrote {out_path}")


def assert_no_text(docx_path: Path) -> None:
    """Sanity check: confirm the produced docx carries no paragraph text."""
    doc = Document(str(docx_path))
    stray = [p.text for p in doc.paragraphs if p.text.strip()]
    if stray:
        raise RuntimeError(f"Text leaked into output docx: {stray}")
    log("Verified: output docx contains zero text runs.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path, help="source .docx or .pdf")
    ap.add_argument("--dpi", type=int, default=300, help="raster DPI, default 300 (print quality)")
    ap.add_argument("--out-prefix", default="output", help="output filename stem, default 'output'")
    ap.add_argument("--out-dir", type=Path, default=None, help="output directory, default = source's directory")
    ap.add_argument("--keep-intermediate-pdf", action="store_true",
                     help="keep the intermediate rendered PDF (docx source only)")
    args = ap.parse_args()

    source = args.source.resolve()
    if not source.exists():
        sys.exit(f"Source not found: {source}")

    out_dir = args.out_dir.resolve() if args.out_dir else source.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    workdir = out_dir / f"{args.out_prefix}_work"
    workdir.mkdir(parents=True, exist_ok=True)
    pages_dir = out_dir / f"{args.out_prefix}_pages"

    try:
        if source.suffix.lower() == ".pdf":
            pdf_path = source
        elif source.suffix.lower() in (".docx", ".doc", ".dotx", ".odt"):
            pdf_path = docx_to_pdf(source, workdir)
        else:
            sys.exit(f"Unsupported source type: {source.suffix}")

        images = pdf_to_page_images(pdf_path, pages_dir, args.dpi)

        out_docx = out_dir / f"{args.out_prefix}.docx"
        out_pdf = out_dir / f"{args.out_prefix}.pdf"

        build_image_only_docx(images, out_docx, args.dpi)
        build_image_only_pdf(images, out_pdf)
        assert_no_text(out_docx)

        if not args.keep_intermediate_pdf and pdf_path != source:
            pdf_path.unlink(missing_ok=True)
        shutil.rmtree(workdir, ignore_errors=True)

        log("Done.")
        log(f"  Image-only DOCX : {out_docx}")
        log(f"  Image-only PDF  : {out_pdf}")
        log(f"  Page PNGs kept  : {pages_dir}  ({len(images)} pages)")

    except Exception as e:
        log(f"FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
