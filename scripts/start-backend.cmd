@echo off
setlocal
set "ROOT=%~dp0.."
cd /d "%ROOT%\backend"

set "VENV_PY=.venv\Scripts\python.exe"
set "GLOBAL_PY=%LocalAppData%\Programs\Python\Python313\python.exe"
set "GLOBAL_PY_FALLBACK=%UserProfile%\AppData\Local\Programs\Python\Python313\python.exe"
set "GLOBAL_PY_ABS=C:\Users\84923\AppData\Local\Programs\Python\Python313\python.exe"
set "UVICORN_ARGS=-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

if exist "%VENV_PY%" (
  "%VENV_PY%" %UVICORN_ARGS%
  if not errorlevel 1 goto :eof
  echo [DUO MIND] Khong khoi dong duoc bang Python trong .venv. Thu Python global...
)

if exist "%GLOBAL_PY%" (
  "%GLOBAL_PY%" %UVICORN_ARGS%
  if not errorlevel 1 goto :eof
  echo [DUO MIND] Python global cung khong khoi dong duoc backend.
  goto :eof
)

if exist "%GLOBAL_PY_FALLBACK%" (
  "%GLOBAL_PY_FALLBACK%" %UVICORN_ARGS%
  if not errorlevel 1 goto :eof
  echo [DUO MIND] Python global fallback cung khong khoi dong duoc backend.
  goto :eof
)

if exist "%GLOBAL_PY_ABS%" (
  "%GLOBAL_PY_ABS%" %UVICORN_ARGS%
  if not errorlevel 1 goto :eof
  echo [DUO MIND] Python global duong dan co dinh cung khong khoi dong duoc backend.
  goto :eof
)

python %UVICORN_ARGS%
