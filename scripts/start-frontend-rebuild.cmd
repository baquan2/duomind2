@echo off
setlocal
set "ROOT=%~dp0.."
cd /d "%ROOT%\frontend"
call npm.cmd run dev:rebuild
