@echo off
echo ========================================
echo  Teste WhatsApp Monitor
echo ========================================
echo.

echo Verificando Node.js...
node --version
if %errorlevel% neq 0 (
    echo ERRO: Node.js nao encontrado!
    pause
    exit /b 1
)

echo.
echo Verificando NPM...
npm --version
if %errorlevel% neq 0 (
    echo ERRO: NPM nao encontrado!
    pause
    exit /b 1
)

echo.
echo Verificando pasta whatsapp-monitor...
if not exist "whatsapp-monitor" (
    echo ERRO: Pasta whatsapp-monitor nao encontrada!
    pause
    exit /b 1
)

echo.
echo Entrando na pasta whatsapp-monitor...
cd whatsapp-monitor

echo.
echo Verificando package.json...
if not exist "package.json" (
    echo ERRO: package.json nao encontrado!
    pause
    exit /b 1
)

echo.
echo Verificando dependencias...
if not exist "node_modules" (
    echo Instalando dependencias...
    call npm install
)

echo.
echo Testando servidor...
echo Iniciando em modo de teste...
node server.js

pause
