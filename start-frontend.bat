@echo off
echo ========================================
echo IntelliWheels - Starting Frontend Server
echo ========================================
echo.
echo Starting Python HTTP server on port 8000...
echo.
echo Frontend will be available at: http://localhost:8000
echo.
echo IMPORTANT: Make sure Flask backend is running on port 5000!
echo If not, run: python app.py (in another terminal)
echo.
echo Press Ctrl+C to stop the server
echo.

python -m http.server 8000

pause

