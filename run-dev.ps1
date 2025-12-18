# Start both frontend and backend development servers
Write-Host "Starting frontend and backend servers..." -ForegroundColor Green

# Start frontend in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\apps\frontend'; pnpm dev"

# Wait a moment before starting backend
Start-Sleep -Seconds 2

# Start backend in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\apps\backend'; python -m uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

Write-Host "`nServers starting in separate windows..." -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
