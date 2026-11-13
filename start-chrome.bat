@echo off
rem Mo Chrome rieng cho app, co cong dieu khien 9222 (chi may nay truy cap duoc).
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" (
  echo Khong tim thay chrome.exe. Sua duong dan trong file nay.
  pause
  exit /b 1
)
start "" "%CHROME%" --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --user-data-dir="%~dp0chrome-profile" https://www.facebook.com/ads/library/ https://app.shophunter.io/shops/track
