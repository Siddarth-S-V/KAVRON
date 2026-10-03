@echo off
setlocal
cd /d "%~dp0Frontend"
if not exist node_modules (
  echo Installing frontend dependencies...
  npm install
)
npm run dev
endlocal
