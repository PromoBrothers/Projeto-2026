# 🔄 RESETAR WHATSAPP - SOLUÇÃO PARA "No sessions"

## ⚠️ PROBLEMA: SessionError: No sessions

Este erro ocorre quando as chaves de sessão do Baileys estão corrompidas.

---

## ✅ SOLUÇÃO: Limpar TUDO e reconectar

### 🚀 OPÇÃO 1: Script Automatizado (RECOMENDADO)

```bash
# Linux/Mac
chmod +x reset_whatsapp.sh
./reset_whatsapp.sh

# Windows
reset_whatsapp.bat
```

O script faz tudo automaticamente e mostra os próximos passos.

---

### 📋 OPÇÃO 2: Comandos Manuais

Execute **exatamente** estes comandos:

### 1️⃣ Parar e limpar TUDO
```bash
cd /caminho/do/PROJETO-V4

# Parar containers
docker-compose down

# Limpar volumes (⚠️ ISSO VAI DESCONECTAR O WHATSAPP!)
docker-compose down -v

# Remover volumes órfãos
docker volume prune -f
```

### 2️⃣ Verificar se limpou
```bash
# Verificar volumes
docker volume ls | grep whatsapp

# NÃO deve aparecer nada!
```

### 3️⃣ Rebuild completo
```bash
# Build do zero
docker-compose build --no-cache

# Subir novamente
docker-compose up -d
```

### 4️⃣ Verificar logs
```bash
# Ver se iniciou corretamente
docker-compose logs -f whatsapp-monitor
```

**Deve aparecer:**
```
🔄 Iniciando conexão com WhatsApp...
✅ Socket criado com sucesso
📱 QR Code gerado! Aguardando escaneamento...
```

### 5️⃣ Escanear QR Code
```bash
# Opção A: Navegador
http://SEU_IP:3001/qr

# Opção B: Terminal (ver o QR)
docker-compose logs -f whatsapp-monitor
```

### 6️⃣ Aguardar conexão
**Deve aparecer:**
```
✅ Conectado ao WhatsApp com sucesso!
```

**NÃO deve aparecer:**
```
❌ SessionError: No sessions  (se aparecer, volte ao passo 1)
❌ Closing open session...     (se aparecer, há 2 instâncias rodando)
```

---

## 🔍 VERIFICAÇÕES

### Verificar que SÓ tem 1 instância:
```bash
docker-compose ps

# Deve mostrar APENAS:
# - whatsapp-monitor (porta 3001)
# - scraper-promo (porta 80)
```

### Verificar status do WhatsApp:
```bash
curl http://localhost:3001/status

# Deve retornar:
{"connected": true, "user": "5511..."}
```

### Testar envio de mensagem:
```bash
# Via interface web
http://SEU_IP/

# Ir em "Produtos Não Agendados"
# Clicar em "Enviar Agora"
# Selecionar um grupo
# Confirmar
```

**Deve funcionar SEM erro "No sessions"**

---

## 🚨 SE AINDA DER ERRO

### Verificar se há processos node rodando:
```bash
docker-compose exec whatsapp-monitor ps aux | grep node
```

### Verificar se o volume está limpo:
```bash
docker-compose exec whatsapp-monitor ls -la /app/auth_info_baileys/

# Se mostrar arquivos antigos, pare e limpe novamente:
docker-compose down -v
docker volume rm projeto-v4_whatsapp-session
```

### Verificar logs completos:
```bash
docker-compose logs whatsapp-monitor | grep -E "SessionError|No sessions|Conectado"
```

---

## ⚡ COMANDOS RÁPIDOS

### Reset rápido:
```bash
docker-compose down -v && \
docker volume prune -f && \
docker-compose build --no-cache && \
docker-compose up -d && \
docker-compose logs -f whatsapp-monitor
```

### Verificar tudo está OK:
```bash
echo "=== Containers ===" && \
docker-compose ps && \
echo "=== Status WhatsApp ===" && \
curl -s http://localhost:3001/status | jq && \
echo "=== Logs recentes ===" && \
docker-compose logs --tail=20 whatsapp-monitor
```

---

## ✅ CHECKLIST

Antes de considerar resolvido:

- [ ] Executou `docker-compose down -v`
- [ ] Executou `docker volume prune -f`
- [ ] Executou `docker-compose build --no-cache`
- [ ] Apenas 2 containers rodando (whatsapp-monitor + scraper-promo)
- [ ] QR Code escaneado
- [ ] Status retorna `{"connected": true}`
- [ ] Teste de envio funcionou SEM erro "No sessions"

---

**Última atualização:** 2025-11-19
