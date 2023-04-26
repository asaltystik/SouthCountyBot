@echo off

rem Get the current directory
set CURRENT_DIR=%~dp0

rem Change to the current directory + the venv folder
cd %CURRENT_DIR%venv

rem Activate the virtual environment
CALL %CURRENT_DIR%venv\Scripts\activate.bat

rem Install the requirements to the virtual environment
pip install -r %CURRENT_DIR%requirements.txt
cls

rem Run the main.py file
python %CURRENT_DIR%main.py
