@echo off

SETLOCAL
REM Check for Python Installation
python --version 2>NUL
IF %ERRORLEVEL%==1 GOTO python_error

REM download dependancy
python downloadDependancy.py
IF %ERRORLEVEL% NEQ 0 GOTO download_error

REM end script
GOTO :end

:python_error
ECHO.
ECHO The Python is not installed:
ECHO.
ECHO Please install Python in your PC.
ECHO.
ECHO [The error occured in %~nx0]
EXIT /B 3

:download_error
ECHO.
ECHO ERROR: Failed to download
ECHO.
ECHO [The error occured in %~nx0]
EXIT /B 1

:end
ENDLOCAL