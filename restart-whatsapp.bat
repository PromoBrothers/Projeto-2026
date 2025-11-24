@echo off
echo ========================================
echo  Reiniciando WhatsApp Monitor
echo ========================================
echo.

echo [1/2] Parando servidor Node.js...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001 ^| findstr LISTENING') do (
    echo Parando processo %%a
    taskkill //F //PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

echo [2/2] Iniciando servidor novamente...
cd whatsapp-monitor
start "WhatsApp Monitor" cmd /k "npm start"

echo.
echo ========================================
echo  Servidor reiniciado!
echo ========================================
echo.
echo Aguarde alguns segundos e recarregue a pagina.
echo.
pause
