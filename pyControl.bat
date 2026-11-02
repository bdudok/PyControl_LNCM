@echo off
rem Starts the pyControl GUI. Double-click it or use a desktop shortcut; it works from any folder.
rem No console window: messages are in the GUI's log, and errors go to ErrorLog.txt in this folder.
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo Could not find .venv in the PyControl folder. Run "uv sync" there first.
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" pyControl_GUI.pyw
