@echo off
echo ========================================
echo  WhatsApp Monitor - Promo Brothers
echo ========================================
echo.

echo [1/3] Verificando instalacao do Node.js...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERRO: Node.js nao encontrado!
    echo Por favor, instale o Node.js: https://nodejs.org/
    pause
    exit /b 1
)

echo [2/3] Instalando dependencias do WhatsApp Monitor...
cd whatsapp-monitor
if not exist node_modules (
    echo Instalando pacotes npm...
    call npm install
    if %errorlevel% neq 0 (
        echo ERRO ao instalar dependencias!
        pause
        exit /b 1
    )
) else (
    echo Dependencias ja instaladas.
)

echo [3/3] Iniciando servidores...
echo.
echo Abrindo terminais separados para:
echo   - WhatsApp Monitor (porta 3001)
echo   - Flask API (porta 5000)
echo.

REM Iniciar WhatsApp Monitor em nova janela
start "WhatsApp Monitor" cmd /k "cd /d %~dp0whatsapp-monitor && npm start"

REM Aguardar 3 segundos
timeout /t 3 /nobreak >nul

REM Iniciar Flask em nova janela
start "Flask API" cmd /k "cd /d %~dp0 && python run.py"

REM Aguardar 5 segundos para os servidores iniciarem
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo  Servidores Iniciados!
echo ========================================
echo.
echo WhatsApp Monitor: http://localhost:3001
echo Flask API: http://localhost:5000
echo Interface: http://localhost:5000/whatsapp-monitor
echo.
echo Abrindo interface no navegador...
start http://localhost:5000/whatsapp-monitor

echo.
echo Pressione qualquer tecla para fechar esta janela.
echo Os servidores continuarao rodando em segundo plano.
pause >nul
