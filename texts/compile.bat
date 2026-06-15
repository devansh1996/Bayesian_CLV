@echo off
setlocal EnableDelayedExpansion

:: Strip the WindowsApps\python.exe entry from PATH (it breaks MiKTeX)
set "CLEAN_PATH="
for %%i in ("%PATH:;=" "%") do (
    set "entry=%%~i"
    if /I "!entry!" NEQ "C:\Users\devan\AppData\Local\Microsoft\WindowsApps\python.exe" (
        if defined CLEAN_PATH (
            set "CLEAN_PATH=!CLEAN_PATH!;!entry!"
        ) else (
            set "CLEAN_PATH=!entry!"
        )
    )
)
set "PATH=!CLEAN_PATH!;C:\Users\devan\AppData\Local\Programs\MiKTeX\miktex\bin\x64"

cd /d "%~dp0"

echo === Pass 1: pdflatex ===
pdflatex --interaction=nonstopmode thesis.tex
if errorlevel 1 goto error

echo === biber ===
biber thesis
if errorlevel 1 goto error

echo === Pass 2: pdflatex ===
pdflatex --interaction=nonstopmode thesis.tex
if errorlevel 1 goto error

echo === Pass 3: pdflatex ===
pdflatex --interaction=nonstopmode thesis.tex
if errorlevel 1 goto error

echo.
echo === Done! thesis.pdf created ===
goto end

:error
echo.
echo === Compilation failed. Check thesis.log for details ===
exit /b 1

:end
endlocal
