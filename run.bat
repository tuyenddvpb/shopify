@echo off
rem Bam dup de chay voi tu khoa trong config.json, hoac: run.bat "tu khoa 1" "tu khoa 2"
cd /d "%~dp0"
python -m adsfinder run %*
pause
