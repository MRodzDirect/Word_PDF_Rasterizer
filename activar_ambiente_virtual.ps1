# Activate the project's virtual environment (ambiente_virtual) for PowerShell.
# Usage: In PowerShell run: `Set-Location 'C:\path\to\project'; .\activar_ambiente_virtual.ps1`
# Or bypass policy from console: `powershell -ExecutionPolicy Bypass -NoProfile -File .\activar_ambiente_virtual.ps1`

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$venvDir = Join-Path $scriptDir 'ambiente_virtual'
$activate = Join-Path $venvDir 'Scripts\Activate.ps1'

if (Test-Path $activate) {
    . $activate
    Write-Output "Activated virtualenv: $venvDir"
    python -c "import sys; print(sys.executable)"
} else {
    Write-Error "Virtual environment Activate.ps1 not found at '$activate'"
    exit 1
}
