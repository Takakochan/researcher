@echo off
setlocal
chcp 65001 > nul
set PYTHONUTF8=1
cd /d "%~dp0"
where uv > nul 2>&1
if %errorlevel%==0 (
    uv run researcher-bot
) else (
    "%USERPROFILE%\.local\bin\uv.exe" run researcher-bot
)
pause
