# SIGNOVA - one-time Windows setup. Run from the SIGNOVA folder:
#   powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Find-Python {
    foreach ($v in "3.11", "3.10", "3.12", "3.9") {
        try {
            & py "-$v" -c "import sys" 2>$null
            if ($LASTEXITCODE -eq 0) { return @{ Exe = "py"; Args = @("-$v") } }
        } catch { }
    }
    try {
        $ok = & python -c "import sys; print(int((3,9) <= sys.version_info[:2] <= (3,12)))" 2>$null
        if ($ok -eq "1") { return @{ Exe = "python"; Args = @() } }
    } catch { }
    return $null
}

Write-Host "== SIGNOVA setup ==" -ForegroundColor Magenta
$py = Find-Python
if (-not $py) {
    Write-Host "Python 3.9-3.12 was not found." -ForegroundColor Red
    Write-Host "Install Python 3.11 from https://www.python.org/downloads/windows/ (tick 'Add python.exe to PATH'), then run this script again."
    exit 1
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    $pyArgs = $py.Args
    & $py.Exe @pyArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create the virtual environment." }
}
$venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host "Installing packages (this can take a few minutes)..."
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Package installation failed. Check your internet connection and that Python is 3.9-3.12." -ForegroundColor Red
    exit 1
}

Write-Host "Running self-test..."
& $venvPy -m unittest discover -s tests -t .

Write-Host ""
Write-Host "Setup complete. Start the app with:  .\run_signova.ps1" -ForegroundColor Green
