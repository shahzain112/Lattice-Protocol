@echo off
echo ==========================================
echo   LATTICE PROJECT - AUTO SETUP SCRIPT
echo ==========================================
echo.

REM Step 1: Go to project folder
cd /d E:\Lattice

REM Step 2: Deactivate if active
call deactivate 2>nul

REM Step 3: Delete old venv
echo [1/6] Purana venv delete kar raha hoon...
rmdir /s /q venv 2>nul
echo      ✅ Purana venv delete ho gaya!
echo.

REM Step 4: Install virtualenv globally
echo [2/6] virtualenv install kar raha hoon...
python -m pip install --user virtualenv >nul 2>&1
echo      ✅ virtualenv install ho gaya!
echo.

REM Step 5: Create new venv using virtualenv
echo [3/6] Naya venv bana raha hoon...
python -m virtualenv venv >nul 2>&1
echo      ✅ Naya venv ban gaya!
echo.

REM Step 6: Activate venv
echo [4/6] venv activate kar raha hoon...
call venv\Scripts\activate.bat
echo      ✅ venv activate ho gaya!
echo.

REM Step 7: Upgrade pip
echo [5/6] pip upgrade kar raha hoon...
python -m pip install --upgrade pip >nul 2>&1
echo      ✅ pip upgrade ho gaya!
echo.

REM Step 8: Install requirements
echo [6/6] requirements.txt se packages install kar raha hoon...
python -m pip install -r requirements.txt
echo      ✅ Sab packages install ho gaye!
echo.

echo ==========================================
echo   ✅ SAB KUCH READY HAI BHAI!
echo ==========================================
echo.
echo Ab bas yeh command chalao:
echo    python main.py
echo.
pause
