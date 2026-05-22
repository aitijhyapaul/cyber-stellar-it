@echo off
REM Local dev launcher for Services Website backend.
REM Uses port 8100 to avoid conflicts with other FastAPI projects (Atashi ERP, ERP SaaS).
cd /d "%~dp0"
call venv\Scripts\activate.bat
uvicorn main:app --host 127.0.0.1 --port 8100 --reload
