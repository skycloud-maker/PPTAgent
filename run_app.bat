@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=C:\codex\python312\python.exe"

echo [INFO] PPTAgent launcher started.

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Bundled Python was not found at:
  echo         %PYTHON_EXE%
  goto fail
)

if not exist ".env" (
  echo [INFO] .env file not found. Creating one from .env.example...
  copy /Y ".env.example" ".env" >nul
)

echo [INFO] Checking required Python packages...
"%PYTHON_EXE%" -c "import importlib.util as u, sys; required=['streamlit','openai','pptx','pydantic','dotenv']; missing=[m for m in required if u.find_spec(m) is None]; print('|'.join(missing)); sys.exit(0 if not missing else 1)"
if errorlevel 1 goto install_deps

goto run_app

:install_deps
echo [INFO] Installing required packages...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Package installation failed.
  echo [NEXT] Check your internet connection and pip access, then try again.
  goto fail
)

echo [INFO] Package installation completed.

:run_app
echo [INFO] Starting PPTAgent Streamlit app...
"%PYTHON_EXE%" -m streamlit run app.py
if errorlevel 1 (
  echo [ERROR] Failed to start the Streamlit app.
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
