#!/bin/bash

# Script para resetar completamente o WhatsApp e resolver erro "No sessions"

echo "========================================="
echo "🔄 RESET COMPLETO DO WHATSAPP"
echo "========================================="
echo ""
echo "⚠️  ATENÇÃO: Isso vai desconectar o WhatsApp!"
echo "Você precisará escanear o QR Code novamente."
echo ""
read -p "Deseja continuar? (s/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Operação cancelada."
    exit 1
fi

echo ""
echo "1️⃣ Parando containers..."
docker-compose down

echo ""
echo "2️⃣ Removendo volumes (isso limpa as sessões corrompidas)..."
docker-compose down -v

echo ""
echo "3️⃣ Removendo volumes órfãos..."
docker volume prune -f

echo ""
echo "4️⃣ Verificando se volumes foram removidos..."
VOLUMES=$(docker volume ls | grep whatsapp || true)
if [ -z "$VOLUMES" ]; then
    echo "✅ Todos os volumes do WhatsApp foram removidos"
else
    echo "⚠️  Ainda existem volumes:"
    echo "$VOLUMES"
    echo ""
    echo "Removendo manualmente..."
    docker volume rm projeto-v4_whatsapp-session 2>/dev/null || true
    docker volume rm projeto_v4_whatsapp-session 2>/dev/null || true
    docker volume rm whatsapp-session 2>/dev/null || true
fi

echo ""
echo "5️⃣ Limpando imagens antigas (rebuild completo)..."
docker-compose build --no-cache

echo ""
echo "6️⃣ Iniciando containers..."
docker-compose up -d

echo ""
echo "7️⃣ Aguardando containers iniciarem (10 segundos)..."
sleep 10

echo ""
echo "8️⃣ Verificando status dos containers..."
docker-compose ps

echo ""
echo "========================================="
echo "✅ RESET CONCLUÍDO!"
echo "========================================="
echo ""
echo "📱 PRÓXIMOS PASSOS:"
echo ""
echo "1. Aguarde 30 segundos para o WhatsApp gerar o QR Code"
echo ""
echo "2. Acesse o QR Code:"
echo "   http://SEU_IP:3001/qr"
echo ""
echo "3. Escaneie com o WhatsApp do celular:"
echo "   - Abra WhatsApp"
echo "   - Toque em 'Aparelhos conectados'"
echo "   - Toque em 'Conectar aparelho'"
echo "   - Escaneie o QR Code"
echo ""
echo "4. Acompanhe os logs:"
echo "   docker-compose logs -f whatsapp-monitor"
echo ""
echo "5. Verifique a conexão:"
echo "   curl http://localhost:3001/status"
echo ""
echo "Deve retornar: {\"connected\": true}"
echo ""
echo "========================================="
