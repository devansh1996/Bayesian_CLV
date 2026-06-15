@echo off
:: Convert Windows path to WSL path and run latexmk via WSL
setlocal
set "WINDOC=%~1"
for /f "delims=" %%p in ('wsl wslpath -a "%WINDOC%.tex"') do set "WSLDOC=%%p"
wsl bash -c "latexmk -pdf -synctex=1 -interaction=nonstopmode -file-line-error '%WSLDOC%'"
endlocal
