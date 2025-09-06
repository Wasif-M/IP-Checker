@echo off
echo Starting DOT 5 with ngrok tunnel...
echo.

REM Start the server in background
echo Starting DOT 5 server...
start "DOT 5 Server" cmd /k "cd /d C:\Users\WasifMehmood\Desktop\test\dot5 && uvicorn server:app --host 127.0.0.1 --port 8000"

REM Wait a moment for server to start
timeout /t 3 /nobreak >nul

REM Start ngrok tunnel
echo Starting ngrok tunnel...
start "ngrok Tunnel" cmd /k "cd /d C:\ngrok && ngrok http 8000"

echo.
echo Both services are starting...
echo.
echo 1. DOT 5 Server: http://127.0.0.1:8000
echo 2. ngrok Tunnel: Check the ngrok window for your public URL
echo.
echo Your app will be publicly accessible via the ngrok URL!
echo.
pause 