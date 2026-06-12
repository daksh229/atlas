# Start the BF Atlas React frontend (Vite dev server, http://localhost:5173)
# The dev server proxies /api -> the backend (default http://localhost:8000).
param([string]$ApiTarget = "http://localhost:8000")
Set-Location "$PSScriptRoot/frontend-react"
$env:VITE_API_TARGET = $ApiTarget
if (-not (Test-Path "node_modules")) { npm install }
npm run dev
