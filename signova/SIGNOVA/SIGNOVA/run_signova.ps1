# Starts SIGNOVA. Usage: powershell -ExecutionPolicy Bypass -File .\run_signova.ps1
Set-Location $PSScriptRoot
$venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Write-Host "Run setup_windows.ps1 first." -ForegroundColor Red
    exit 1
}
& $venvPy -m streamlit run app.py
