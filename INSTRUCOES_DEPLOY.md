# 🚀 INSTRUÇÕES DE DEPLOY - SERVIDOR

## ⚠️ IMPORTANTE: Ordem de execução

Siga **exatamente** esta ordem para evitar o erro "No sessions":

---

## 📋 **PASSO 1: Subir os containers**

```bash
# Na pasta do projeto
cd PROJETO-V4

# Parar containers antigos (se houver)
docker-compose down -v

# Build e iniciar
docker-compose up -d --build

# Verificar se subiram
docker-compose ps
```

**Resultado esperado:**
```
NAME                STATUS
whatsapp-monitor    Up
scraper-promo       Up
```

---

## 📱 **PASSO 2: Conectar o WhatsApp (QR Code)**

### Opção A - Via navegador:
```
http://SEU_IP:3001/qr
```

### Opção B - Via terminal:
```bash
docker-compose logs -f whatsapp-monitor
```

**Ação necessária:**
1. Abra o WhatsApp no celular
2. Toque em **Aparelhos conectados**
3. Toque em **Conectar aparelho**
4. Escaneie o QR Code

**Aguarde aparecer a mensagem:**
```
✅ WhatsApp conectado!
```

---

## ✅ **PASSO 3: Verificar conexão**

```bash
# Verificar status do WhatsApp
curl http://localhost:3001/status

# Deve retornar:
{"connected": true, "user": "55..."}
```

---

## 🎯 **PASSO 4: Configurar grupos fixos**

1. Acesse: `http://SEU_IP/`
2. Vá em **Configurações WhatsApp** → **Grupos Fixos**
3. Adicione os grupos que receberão mensagens automáticas
4. Marque como **Ativo**
5. Salve

---

## 📨 **PASSO 5: Testar envio**

### Teste 1 - Envio manual:
1. Vá em **Produtos Não Agendados**
2. Clique em qualquer produto
3. Clique **Enviar Agora**
4. Selecione os grupos
5. Confirme

**Se aparecer erro "No sessions":**
- ❌ WhatsApp não está conectado
- ✅ Volte ao PASSO 2 e escaneie o QR Code

### Teste 2 - Envio agendado:
1. Vá em **Produtos Não Agendados**
2. Agende um produto para **+1 minuto**
3. Aguarde o scheduler processar (verifica a cada 30s)
4. Verifique os logs:

```bash
docker-compose logs -f scraper-promo | grep scheduler
```

**Deve aparecer:**
```
✅ Scheduler de mensagens iniciado
⏰ Horário atingido para produto: ...
✅ Mensagem enviada e agendamento removido
```

---

## 🔍 **TROUBLESHOOTING**

### Erro: "No sessions"

**Causa:** WhatsApp não está conectado

**Solução:**
```bash
# 1. Verificar status
curl http://localhost:3001/status

# 2. Se retornar {"connected": false}
# Acesse http://SEU_IP:3001/qr e escaneie novamente

# 3. Verificar logs
docker-compose logs -f whatsapp-monitor
```

### Erro: "WhatsApp Monitor não está acessível"

**Causa:** Container do WhatsApp não está rodando

**Solução:**
```bash
# Verificar containers
docker-compose ps

# Reiniciar se necessário
docker-compose restart whatsapp-monitor
```

### Mensagens não são enviadas automaticamente

**Verificações:**
1. ✅ WhatsApp está conectado (`/status` retorna `connected: true`)
2. ✅ Grupos fixos estão configurados e **ativos**
3. ✅ Scheduler está rodando (veja nos logs do scraper-promo)
4. ✅ Produto tem horário de agendamento configurado

**Ver logs do scheduler:**
```bash
docker-compose logs -f scraper-promo | grep -E "scheduler|agendad|Enviado"
```

---

## 📊 **MONITORAMENTO**

### Ver todos os logs:
```bash
docker-compose logs -f
```

### Ver logs específicos:
```bash
# Flask (scraper)
docker-compose logs -f scraper-promo

# WhatsApp Monitor
docker-compose logs -f whatsapp-monitor
```

### Verificar saúde dos containers:
```bash
docker-compose ps
docker stats
```

---

## 🔄 **REINICIAR TUDO**

Se algo der errado, reinicie tudo:

```bash
# Parar tudo
docker-compose down

# Limpar volumes (⚠️ ISSO VAI DESCONECTAR O WHATSAPP)
docker-compose down -v

# Subir novamente
docker-compose up -d --build

# Escaneie o QR Code novamente
```

---

## 🎯 **URLs IMPORTANTES**

| Serviço | URL |
|---------|-----|
| Interface Web | http://SEU_IP |
| QR Code | http://SEU_IP:3001/qr |
| Status WhatsApp | http://SEU_IP:3001/status |

---

## ✅ **CHECKLIST FINAL**

Antes de considerar o deploy concluído:

- [ ] 2 containers rodando (whatsapp-monitor, scraper-promo)
- [ ] QR Code escaneado e WhatsApp conectado
- [ ] Status retorna `{"connected": true}`
- [ ] Grupos fixos configurados no sistema
- [ ] Teste de envio manual funcionou
- [ ] Teste de envio agendado funcionou
- [ ] Scheduler está rodando (verificar logs)

---

## 🆘 **SUPORTE**

Se ainda tiver problemas:

1. Capture os logs:
```bash
docker-compose logs > logs.txt
```

2. Verifique as variáveis de ambiente:
```bash
docker-compose config
```

3. Verifique a conectividade:
```bash
curl http://localhost:3001/status
curl http://localhost/
```

---

**Última atualização:** 2025-11-19
