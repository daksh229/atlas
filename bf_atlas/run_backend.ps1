# Start the BF Atlas FastAPI backend (http://localhost:8000, docs at /docs)
param([int]$Port = 8000)
Set-Location "$PSScriptRoot/backend"
$env:PYTHONPATH = "."
uvicorn app.main:app --reload --port $Port
