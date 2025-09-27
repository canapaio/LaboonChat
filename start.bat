@echo off
REM LaboonChat Windows Launcher
REM =============================
REM 🐋 Faithful connections across digital oceans 🌊

echo.
echo    🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊
echo    🌊                                            🌊
echo    🌊        🐋 LaboonChat 🐋                   🌊
echo    🌊                                            🌊
echo    🌊    "Faithful connections across           🌊
echo    🌊         digital oceans"                   🌊
echo    🌊                                            🌊
echo    🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non trovato! Installa Python 3.9+ da https://python.org
    pause
    exit /b 1
)

REM Check if LaboonChat is installed
python -c "import laboon_chat" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installazione LaboonChat in corso...
    pip install -e .
    if errorlevel 1 (
        echo ❌ Errore durante l'installazione!
        pause
        exit /b 1
    )
)

echo 🚀 Avvio LaboonChat...
echo.

REM Start LaboonChat
python -m laboon_chat.launcher.laboon_launcher

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo ❌ LaboonChat si è chiuso con errori
    pause
)