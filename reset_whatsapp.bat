@echo off
chcp 65001 >nul
cls

echo =========================================
echo 🔄 RESET COMPLETO DO WHATSAPP
echo =========================================
echo.
echo ⚠️  ATENÇÃO: Isso vai desconectar o WhatsApp!
echo Você precisará escanear o QR Code novamente.
echo.
set /p confirm="Deseja continuar? (s/n): "

if /i not "%confirm%"=="s" (
    echo ❌ Operação cancelada.
    exit /b 1
)

echo.
echo 1️⃣ Parando containers...
docker-compose down

echo.
echo 2️⃣ Removendo volumes (isso limpa as sessões corrompidas)...
docker-compose down -v

echo.
echo 3️⃣ Removendo volumes órfãos...
docker volume prune -f

echo.
echo 4️⃣ Verificando se volumes foram removidos...
docker volume ls | findstr whatsapp
if %errorlevel% equ 0 (
    echo ⚠️  Ainda existem volumes do WhatsApp
    echo Removendo manualmente...
    docker volume rm projeto-v4_whatsapp-session 2>nul
    docker volume rm projeto_v4_whatsapp-session 2>nul
    docker volume rm whatsapp-session 2>nul
    echo ✅ Volumes removidos manualmente
) else (
    echo ✅ Todos os volumes do WhatsApp foram removidos
)

echo.
echo 5️⃣ Limpando imagens antigas (rebuild completo)...
docker-compose build --no-cache

echo.
echo 6️⃣ Iniciando containers...
docker-compose up -d

echo.
echo 7️⃣ Aguardando containers iniciarem (10 segundos)...
timeout /t 10 /nobreak >nul

echo.
echo 8️⃣ Verificando status dos containers...
docker-compose ps

echo.
echo =========================================
echo ✅ RESET CONCLUÍDO!
echo =========================================
echo.
echo 📱 PRÓXIMOS PASSOS:
echo.
echo 1. Aguarde 30 segundos para o WhatsApp gerar o QR Code
echo.
echo 2. Acesse o QR Code:
echo    http://SEU_IP:3001/qr
echo.
echo 3. Escaneie com o WhatsApp do celular:
echo    - Abra WhatsApp
echo    - Toque em 'Aparelhos conectados'
echo    - Toque em 'Conectar aparelho'
echo    - Escaneie o QR Code
echo.
echo 4. Acompanhe os logs:
echo    docker-compose logs -f whatsapp-monitor
echo.
echo 5. Verifique a conexão:
echo    curl http://localhost:3001/status
echo.
echo Deve retornar: {"connected": true}
echo.
echo =========================================
echo.
pause
