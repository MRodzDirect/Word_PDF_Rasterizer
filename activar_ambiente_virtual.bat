@echo off
rem Activate the project's virtual environment (ambiente_virtual).
rem Run this from Command Prompt (cmd.exe) in the project folder to activate.

set "VENV_DIR=%~dp0ambiente_virtual"
if exist "%VENV_DIR%\Scripts\activate.bat" (
	call "%VENV_DIR%\Scripts\activate.bat"
) else (
	echo Virtual environment not found at "%VENV_DIR%\Scripts\activate.bat"
	exit /b 1
)

rem Print Python executable used (optional quick verification)
python -c "import sys; print(sys.executable)"