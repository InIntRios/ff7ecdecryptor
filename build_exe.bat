@echo off
setlocal enabledelayedexpansion

title Building FF7EC Asset Decryptor Executable
echo ===============================================================================
echo            BUILDING FF7EC ASSET DECRYPTOR STANDALONE EXECUTABLE (.EXE)
echo ===============================================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found in your system PATH.
    echo Please download and install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/4] Checking Python environment...
python --version

:: 2. Check & extract app.ico if missing
if not exist "app.ico" (
    echo [2/4] Icon "app.ico" not found. Extracting icon from FF7EC.exe...
    if exist "tools\extract_icon.py" (
        python tools\extract_icon.py
    )
) else (
    echo [2/4] Found icon: app.ico
)

:: 3. Check / Install PyInstaller
echo [3/4] Checking PyInstaller...
python -m PyInstaller --version >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [*] PyInstaller not detected. Installing PyInstaller...
    python -m pip install --upgrade pyinstaller
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install PyInstaller. Please check your internet connection.
        pause
        exit /b 1
    )
)

:: 4. Compile Standalone Executable
echo [4/4] Compiling FF7EC_Decryptor.exe with PyInstaller...
python -m PyInstaller --noconfirm --clean FF7EC_Decryptor.spec

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Build failed during PyInstaller compilation.
    pause
    exit /b %ERRORLEVEL%
)

:: 5. Copy output executable to root directory
if exist "dist\FF7EC_Decryptor.exe" (
    echo.
    echo [*] Copying compiled executable to root directory...
    taskkill /f /im FF7EC_Decryptor.exe >nul 2>nul
    copy /y "dist\FF7EC_Decryptor.exe" ".\FF7EC_Decryptor.exe" >nul
    :: 6. Apply Authenticode digital signature & timestamp
    echo [*] Applying Authenticode digital signature and timestamp...
    if exist "tools\sign_exe.ps1" (
        powershell -NoProfile -ExecutionPolicy Bypass -File "tools\sign_exe.ps1" -FilePath ".\FF7EC_Decryptor.exe"
    )
    ie4uinit.exe -show >nul 2>nul
    python -c "import ctypes; ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)" >nul 2>nul
    echo.
    echo ===============================================================================
    echo                       BUILD COMPLETED SUCCESSFULLY!
    echo ===============================================================================
    echo Output executable: %~dp0FF7EC_Decryptor.exe
    echo You can now run FF7EC_Decryptor.exe directly without Python installed.
    echo ===============================================================================
) else (
    echo [WARNING] dist\FF7EC_Decryptor.exe was not found.
)

echo.
pause
