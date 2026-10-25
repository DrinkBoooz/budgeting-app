@echo off
cd /d "%~dp0"
echo ========================================================
echo Compiling Budgeting & Salary Suite into Standalone EXE
echo ========================================================

if not exist .venv (
    echo Error: .venv virtual environment not found! Run python -m venv .venv first.
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Removing old builds...
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist

echo Initiating Compilation with PyInstaller...
python -m PyInstaller --noconfirm --clean budget_app.spec

if not exist dist mkdir dist

echo ========================================================
echo Done! Check the dist/ folder for "Budgeting App.exe"
echo ========================================================
if "%1" neq "--nopause" pause
