@echo off
echo Starting WS Intelligence Platform...
echo.

REM Start the FastAPI backend using the virtual environment
echo [1/2] Starting Python API backend on http://localhost:8000
start "WS-API" cmd /k "cd /d c:\ai-jobs\wealthsimple\app && .venv\Scripts\python.exe -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment for the API to start
timeout /t 5 /nobreak > NUL

REM Start the Next.js frontend
echo [2/2] Starting Next.js frontend on http://localhost:3000
start "WS-Frontend" cmd /k "cd /d c:\ai-jobs\wealthsimple\app\frontend && npm run dev"

echo.
echo Platform is starting... Open http://localhost:3000
