@echo off
title EduQuiz Suite Launcher

:: Force execution from the script's folder
cd /d "%~dp0"

echo ====================================================
echo             EduQuiz Assessment Suite
echo ====================================================
echo.

:: 1. Check if Python is available
python --version >nul 2>&1
if %errorlevel%==0 goto VERIFY_LIBRARIES

echo [!] Python is not detected on this system.
echo [*] Downloading and installing Python silently...

:: Download official lightweight Python installer
curl -o python_installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

echo [*] Running installation (this takes about 1-2 minutes)...
start /wait python_installer.exe /quiet PrependPath=1 Include_test=0

:: Clean up the installer
del python_installer.exe

:: Force-feed the new installation paths directly into this session's environment
set "PATH=%PATH%;%LocalAppData%\Programs\Python\Python311\Scripts\;%LocalAppData%\Programs\Python\Python311\;%ProgramFiles%\Python311\Scripts\;%ProgramFiles%\Python311\"

echo [+][🎉] Python installation complete!
echo.

:VERIFY_LIBRARIES
:: 2. Check and install necessary Python dependencies
echo [*] Verifying required library configurations...
python -m pip install --upgrade pip --quiet
python -m pip install streamlit pandas openpyxl python-docx --quiet

echo.
echo ====================================================
echo [🎉] System is ready! Launching EduQuiz Portal...
echo ====================================================
echo.

:: 3. Execute your background bootstrapper
py run_app.py

:: If the app crashes on launch, pause so we can read the traceback error
if %errorlevel% neq 0 (
    echo.
    echo [!] The app encountered an execution issue.
    pause
)