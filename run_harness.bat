@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=C:\codex\python312\python.exe"

echo [INFO] PPTAgent harness launcher started.

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Bundled Python was not found at:
  echo         %PYTHON_EXE%
  goto fail
)

echo [INFO] Checking required Python packages...
"%PYTHON_EXE%" -c "import importlib.util as u, sys; required=['streamlit','openai','pptx','pydantic','dotenv']; missing=[m for m in required if u.find_spec(m) is None]; print('|'.join(missing)); sys.exit(0 if not missing else 1)"
if errorlevel 1 goto install_deps

goto run_harness

:install_deps
echo [INFO] Installing required packages...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Package installation failed.
  echo [NEXT] Check your internet connection and pip access, then try again.
  goto fail
)

echo [INFO] Package installation completed.

:run_harness
echo [INFO] Running harness cases...
"%PYTHON_EXE%" harness\run_manual_eval.py
if errorlevel 1 (
  echo [ERROR] Harness execution failed.
  goto fail
)

goto end

:fail
echo.
echo Press any key to close this window...
pause >nul
exit /b 1

:end
endlocal
