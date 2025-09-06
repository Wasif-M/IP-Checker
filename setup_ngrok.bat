@echo off
echo Setting up ngrok for DOT 5...
echo.

REM Create ngrok directory
if not exist "C:\ngrok" mkdir "C:\ngrok"
cd /d "C:\ngrok"

REM Download ngrok
echo Downloading ngrok...
powershell -Command "Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip' -OutFile 'ngrok.zip'"

REM Extract ngrok
echo Extracting ngrok...
powershell -Command "Expand-Archive -Path 'ngrok.zip' -DestinationPath '.' -Force"

REM Clean up zip file
del ngrok.zip

REM Set up authentication
echo Setting up authentication...
ngrok config add-authtoken 31QU5MaAsze0eLHCOLXOZKY4oSm_4MqUhNRzAXh6tKRhmfuEd

echo.
echo ngrok setup complete!
echo.
echo To start ngrok tunnel, run:
echo cd C:\ngrok
echo ngrok http 8000
echo.
pause 