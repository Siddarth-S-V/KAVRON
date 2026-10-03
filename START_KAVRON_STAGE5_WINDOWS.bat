@echo off
setlocal
cd /d "%~dp0kavron_backend_complete"
if not exist .venv\Scripts\python.exe (
  echo Creating Python environment...
  py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if exist requirements-stage3.txt python -m pip install -r requirements-stage3.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
endlocal
