@echo off
setlocal
set "ROOT=%~dp0.."

start "DUO MIND Backend" cmd /k "cd /d ""%ROOT%"" && call scripts\start-backend.cmd"
start "DUO MIND Frontend" cmd /k "cd /d ""%ROOT%\frontend"" && npm.cmd run dev"

echo Dang mo backend va frontend trong hai cua so rieng.
echo Sau khi thay backend healthy va frontend ready, mo http://localhost:3001
