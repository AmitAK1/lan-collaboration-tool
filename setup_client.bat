@echo off
title LAN Collaboration - First Time Setup
color 0E
echo ========================================
echo   LAN Collaboration Tool
echo   First Time Setup for Clients
echo ========================================
echo.
echo This will install all required libraries...
echo.
pause

echo.
echo [1/5] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [2/5] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [3/5] Installing numpy...
pip install numpy>=1.24.0

echo.
echo [4/5] Installing pyaudio...
pip install pyaudio>=0.2.13
if %errorlevel% neq 0 (
    echo.
    echo WARNING: PyAudio installation failed!
    echo You may need to install it manually from:
    echo https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
    echo.
)

echo.
echo [5/5] Installing remaining libraries...
pip install Pillow>=10.0.0
pip install mss>=9.0.0
pip install opencv-python>=4.8.0

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Testing installation...
python -c "import numpy, pyaudio, PIL, mss, cv2; print('✓ All libraries installed successfully!')"

if %errorlevel% equ 0 (
    echo.
    echo ✓ Setup completed successfully!
    echo.
    echo You can now run the client using:
    echo   - start_client.bat
    echo   - python client.py
    echo.
) else (
    echo.
    echo ✗ Some libraries failed to install.
    echo Please check the error messages above.
    echo.
)

pause
