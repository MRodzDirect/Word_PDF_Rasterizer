# Rasterizador de Documentos (DOCX/PDF → Imágenes)

Herramienta que convierte documentos Word (`.docx`) o PDF en un nuevo `.docx` y un nuevo `.pdf` donde **todo el contenido es imágenes de página completa**, sin texto editable ni capa de texto oculta. No se ejecuta OCR en ningún punto del proceso.

---

## Requisitos

### 1. Dependencias Python

```bash
pip install -r requirements.txt
```

### 2. Herramientas Externas (Obligatorias)

| Herramienta | Versión recomendada | Ruta recomendada para el PATH | Notas |
|---|---|---|---|
| **Poppler** | 26.02.0 o superior | `C:\Program Files\poppler-26.02.0\Library\bin` | Proporciona `pdftoppm.exe` |
| **LibreOffice** (Portable o instalado) | Última versión | `C:\LibreOfficePortable\App\libreoffice\program` | Proporciona `soffice.exe` |

**Importante:** Ambas carpetas deben estar agregadas al **PATH del sistema**. Si `soffice` no está en el PATH, el script cae automáticamente a la ruta fija definida en la constante `SOFFICE_EXE` dentro de `rasterize_docx.py` — edítala si tu instalación está en otro lugar.

---

## Instalación y Configuración

### Paso 1: Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### Paso 2: Configurar Poppler

1. Agrega esta carpeta al PATH:
```
C:\Program Files\poppler-26.02.0\Library\bin
```
2. Verifica:
```bash
pdftoppm -v
```

### Paso 3: Configurar LibreOffice

1. Descarga **LibreOffice** o **LibreOffice Portable**.
2. Agrega la ruta de la carpeta `program` al PATH del sistema, por ejemplo:
```
C:\LibreOfficePortable\App\libreoffice\program
```
3. Verifica:
```bash
soffice --version
```
4. Si no quieres tocar el PATH del sistema, en su lugar abre `rasterize_docx.py` y ajusta la constante `SOFFICE_EXE` con la ruta completa a tu `soffice.exe`. El script usa el PATH primero y esa constante como respaldo automático.

---

## Uso

```bash
python rasterize_docx.py documento.docx
python rasterize_docx.py documento.pdf --dpi 300
```

### Opciones disponibles

- `--dpi 300` → Calidad de imagen en DPI (por defecto 300, recomendado para impresión)
- `--out-prefix nombre` → Prefijo de los archivos de salida (por defecto `output`)
- `--out-dir carpeta` → Carpeta de destino (por defecto, la misma del archivo fuente)
- `--keep-intermediate-pdf` → Conserva el PDF intermedio generado al convertir un `.docx` (por defecto se borra)

---

## Estructura del Proyecto

```
rasterize_docx/
├── rasterize_docx.py
├── requirements.txt
├── README.md
├── output_pages/     # Imágenes PNG de cada página (una por página, en orden)
├── output.docx       # Documento final (solo imágenes, sin texto)
└── output.pdf        # PDF final (solo imágenes, sin capa de texto)
```

`output_pages/` se conserva después de correr el script — útil si quieres inspeccionar o reutilizar las páginas rasterizadas por separado.

---

## Cómo funciona (resumen del proceso)

1. `.docx` → `.pdf` intermedio, vía LibreOffice headless (render puro, sin OCR).
2. `.pdf` → una imagen PNG por página, vía `pdftoppm`, en alta resolución.
3. Las imágenes se insertan en un `.docx` nuevo (una por página, con salto de página entre cada una) y en un `.pdf` nuevo (vía `img2pdf`, embebido sin pérdida).
4. El script verifica automáticamente que el `.docx` final no contenga ningún texto (`assert_no_text`), como comprobación final.

---

## Notas Importantes

- Todo el proceso es **local** y evita cualquier capa de texto: convertimos el documento a imágenes de alta calidad, sin OCR ni texto editable en el resultado.
- Se respeta el orden de las páginas y el tamaño/orientación original de cada una (cada página puede tener su propia sección con su propio tamaño, para no deformar contenido mixto portrait/landscape).
- El resultado no es accesible por lectores de pantalla ni buscable por texto — es una limitación inherente al ser solo imágenes, no un defecto del script.
- Compatible con Windows, macOS y Linux, siempre que `soffice` y `pdftoppm` estén disponibles (por PATH o por la constante `SOFFICE_EXE`).

---

**¿Listo para usar?**

Ejecuta:
```bash
python rasterize_docx.py tu_archivo.docx
```

Cualquier problema con las rutas de Poppler o LibreOffice, revisa la sección de configuración.
