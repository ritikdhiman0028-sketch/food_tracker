@echo off
:: Run Food Tracker on Windows
:: Auto-installs Python 3 and Flask if missing

cd /d "%~dp0"

:: ── Check for Python ────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Downloading and installing Python 3...

    :: Download Python installer via PowerShell
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"

    if not exist "%TEMP%\python_installer.exe" (
        echo ERROR: Failed to download Python installer.
        echo Please install Python manually: https://www.python.org/downloads/
        pause
        exit /b 1
    )

    :: Install silently, add to PATH, install pip
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1

    :: Refresh PATH so python is found in this session
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"

    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: Python installation may have succeeded but a restart is needed.
        echo Please restart your computer and run this script again.
        pause
        exit /b 1
    )
    echo Python installed successfully.
)

:: ── Install Flask ────────────────────────────────────────────────────────────
echo Checking Flask...
python -m pip install flask --quiet

:: ── Launch app ───────────────────────────────────────────────────────────────
echo.
echo Starting Food Tracker -^> http://localhost:5000
echo.
set PYTHONDONTWRITEBYTECODE=1
python app.py
pause
