@echo off
setlocal
set "ROOT=%~dp0.."

for /f "tokens=5" %%p in ('netstat -ano ^| findstr :3001 ^| findstr LISTENING') do (
  echo Dang dung process %%p tren cong 3001...
  taskkill /PID %%p /F >nul 2>&1
)

cd /d "%ROOT%\frontend"
call npm.cmd run dev:rebuild
