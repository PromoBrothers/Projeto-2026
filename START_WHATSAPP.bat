@echo off
echo ========================================
echo  WhatsApp Monitor - Inicializacao
echo ========================================
echo.

REM Matar processos Node antigos
echo [1/3] Finalizando processos antigos...
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Ir para pasta do WhatsApp Monitor
cd /d "%~dp0whatsapp-monitor"

REM Iniciar servidor
echo [2/3] Iniciando WhatsApp Monitor na porta 3001...
echo.
echo Aguarde o QR Code aparecer...
echo Depois escaneie com seu WhatsApp
echo.
echo [3/3] Servidor iniciando...
echo.

node server.js

pause
