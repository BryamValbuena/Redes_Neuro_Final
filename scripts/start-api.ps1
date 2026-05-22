Set-Location $PSScriptRoot\..
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
