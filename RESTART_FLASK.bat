@echo off
echo ========================================
echo  REINICIANDO FLASK
echo ========================================
echo.

echo Parando processos Python...
taskkill /F /FI "WINDOWTITLE eq *python*" 2>nul
timeout /t 2 /nobreak >nul

echo Iniciando Flask novamente...
start cmd /k "python run.py"

echo.
echo ========================================
echo  Flask reiniciado com sucesso!
echo  Acesse: http://localhost:5000
echo ========================================
pause
