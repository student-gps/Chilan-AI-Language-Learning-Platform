$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Main = Join-Path $ProjectRoot "backend\main.py"

if (-not (Test-Path $Python)) {
    throw "Project virtual environment not found at $Python. Run: py -3.11 -m venv .venv"
}

& $Python $Main
