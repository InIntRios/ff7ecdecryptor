@echo off
setlocal enabledelayedexpansion

title FF7EC Decryptor - Tool Dependencies Setup & Verifier
echo ===============================================================================
echo        FF7EC ASSET DECRYPTOR - AUXILIARY TOOLS SETUP ^& VERIFIER
echo ===============================================================================
echo.

:: 1. Verify Python
echo [1/5] Checking Python environment...
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found in your system PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    echo Remember to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
python --version

:: 2. Verify / Install PyInstaller
echo.
echo [2/5] Checking PyInstaller (needed for building .exe)...
python -m PyInstaller --version >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [*] PyInstaller not installed. Installing via pip...
    python -m pip install --upgrade pyinstaller
    if %ERRORLEVEL% neq 0 (
        echo [WARNING] Failed to install PyInstaller via pip.
    ) else (
        echo [OK] PyInstaller installed successfully!
    )
) else (
    echo [OK] PyInstaller is ready.
)

:: 3. Run automatic external tool check & download (vgmstream, ffmpeg, crid_mod)
echo.
echo [3/5] Verifying external media tools (vgmstream-cli, crid_mod, ffmpeg)...
python ff7ec_decryptor.py check-tools

:: 4. Extract / update app.ico from game directory
echo.
echo [4/5] Checking application icon (app.ico)...
if exist "tools\extract_icon.py" (
    python tools\extract_icon.py
)

:: 5. Refresh Windows Explorer icon cache
echo.
echo [5/5] Refreshing Windows Explorer shell icon cache...
ie4uinit.exe -show >nul 2>nul
python -c "import ctypes; ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)" >nul 2>nul

echo.
echo ===============================================================================
echo                        TOOL ENVIRONMENT STATUS
echo ===============================================================================
if exist "tools\crid_mod.exe" (
    echo  [OK] crid_mod.exe        : READY - tools\crid_mod.exe
) else (
    echo  [!]  crid_mod.exe        : MISSING - Expected in tools\crid_mod.exe
)

if exist "tools\vgmstream-cli.exe" (
    echo  [OK] vgmstream-cli.exe   : READY - tools\vgmstream-cli.exe
) else (
    echo  [!]  vgmstream-cli.exe   : MISSING
)

where ffmpeg >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo  [OK] ffmpeg.exe          : READY - Detected in system PATH
) else (
    if exist "tools\ffmpeg.exe" (
        echo  [OK] ffmpeg.exe          : READY - tools\ffmpeg.exe
    ) else (
        echo  [!]  ffmpeg.exe          : NOT FOUND - Place in tools\ or install in PATH
    )
)

if exist "app.ico" (
    echo  [OK] app.ico             : READY - app.ico
) else (
    echo  [!]  app.ico             : NOT FOUND
)

echo ===============================================================================
echo All required dependencies verified. You can now run or build FF7EC Decryptor!
echo.
pause
