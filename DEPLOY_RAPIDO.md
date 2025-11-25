# 🚀 DEPLOY RÁPIDO - Guia de 15 Minutos

## 📋 Pré-requisitos

Antes de começar, tenha em mãos:

- ✅ IP do servidor (ex: 123.456.789.0)
- ✅ Acesso SSH ao servidor
- ✅ Conta Supabase criada
- ✅ Cookies do Mercado Livre atualizados

---

## ⚡ DEPLOY EM 5 PASSOS

### **PASSO 1: Preparar Servidor (5 min)**

```bash
# Conectar ao servidor
ssh root@SEU_IP

# Instalar tudo de uma vez
curl -fsSL https://get.docker.com | sh && \
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && \
sudo chmod +x /usr/local/bin/docker-compose && \
sudo apt install git -y

# Clonar projeto
git clone https://github.com/seu-usuario/Projeto-2026.git
cd Projeto-2026
```

---

### **PASSO 2: Configurar .env (3 min)**

```bash
# Criar arquivo .env
nano .env
```

**Cole este template e preencha os valores:**

```env
# SUPABASE (OBRIGATÓRIO)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_BUCKET_NAME=imagens_melhoradas_tech

# MERCADO LIVRE (OBRIGATÓRIO para clonagem)
MERCADOLIVRE_AFFILIATE_ID=gabrielvilelaluiz
ML_CSRF_TOKEN=seu-csrf-token
ML_COOKIE__CSRF=seu-csrf-cookie
ML_COOKIE_ORGNICKP=seu-nickname
ML_COOKIE_ORGUSERIDP=seu-userid
# ... (copie TODOS os cookies do navegador)

# AMAZON (OPCIONAL)
AMAZON_ASSOCIATES_TAG=promobrothers-20
SCRAPERAPI_KEY=sua-api-key

# WHATSAPP
WHATSAPP_MONITOR_URL=http://whatsapp-monitor:3001
BAILEYS_API_URL=http://whatsapp-monitor:3001

# FLASK
PORT=5000
FLASK_ENV=production
FLASK_DEBUG=False
LOGIN_USERNAME=admin
LOGIN_PASSWORD=SuaSenhaForte123

# USER AGENT
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# OUTROS
WEBHOOK_URL=
USE_PROXY=false
```

**Salvar:** `Ctrl+O` → `Enter` → `Ctrl+X`

---

### **PASSO 3: Subir Containers (2 min)**

```bash
# Build e iniciar
docker-compose up -d --build

# Aguardar ~30 segundos para inicializar

# Verificar status
docker-compose ps
```

**Resultado esperado:**
```
NAME                STATUS
scraper-promo       Up
whatsapp-monitor    Up
```

---

### **PASSO 4: Conectar WhatsApp (2 min)**

```bash
# Opção A - Ver QR Code no browser:
# http://SEU_IP:3001/qr

# Opção B - Ver QR Code no terminal:
docker-compose logs -f whatsapp-monitor
```

**Ações:**
1. Abrir WhatsApp no celular
2. **Menu** → **Aparelhos conectados**
3. **Conectar aparelho**
4. Escanear QR Code

**Aguardar mensagem:**
```
✅ Conectado ao WhatsApp com sucesso!
```

---

### **PASSO 5: Testar Sistema (3 min)**

```bash
# 1. Verificar WhatsApp conectado
curl http://localhost:3001/status
# Deve retornar: {"connected": true, ...}

# 2. Acessar interface web
# http://SEU_IP
# Login: admin / SuaSenhaForte123

# 3. Adicionar produto teste
# Cole URL do ML ou Amazon

# 4. Enviar mensagem teste
# Clique "Enviar Agora" → Selecione grupo
```

---

## ✅ PRONTO!

Seu sistema está no ar! 🎉

### **URLs Importantes:**

| Serviço | URL |
|---------|-----|
| Interface Web | http://SEU_IP |
| QR Code WhatsApp | http://SEU_IP:3001/qr |
| Status WhatsApp | http://SEU_IP:3001/status |

---

## 🔧 Configurações Pós-Deploy

### **1. Configurar Firewall (Recomendado)**

```bash
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 3001  # WhatsApp QR
```

### **2. Adicionar Grupos ao Monitoramento**

1. Acesse: http://SEU_IP/configuracoes
2. Vá em **Grupos Automáticos**
3. Clique **Adicionar Grupo**
4. Selecione os grupos desejados
5. Salvar

### **3. Configurar Agendamento Automático**

1. Acesse: http://SEU_IP/configuracoes
2. Marque grupos como **Ativo**
3. Configure intervalo de envio (padrão: 5 min)
4. Salvar

---

## 📊 Verificar Logs

```bash
# Ver tudo
docker-compose logs -f

# Apenas Flask
docker-compose logs -f scraper-promo

# Apenas WhatsApp
docker-compose logs -f whatsapp-monitor

# Filtrar erros
docker-compose logs | grep ERROR
```

---

## 🐛 Problemas Comuns

### ❌ WhatsApp não conecta

```bash
# Limpar sessão e tentar novamente
docker-compose down -v
docker-compose up -d
# Escanear QR Code novamente
```

### ❌ Porta 80 ocupada

```bash
# Verificar o que está usando
sudo lsof -i :80

# Parar Apache (se instalado)
sudo systemctl stop apache2

# Reiniciar containers
docker-compose restart
```

### ❌ "No sessions" ao enviar

**Causa:** WhatsApp desconectou

**Solução:**
1. Acesse: http://SEU_IP:3001/qr
2. Escaneie QR Code novamente

### ❌ Link de afiliado ML não gera

**Causa:** Cookies expirados (expiram a cada ~30 dias)

**Solução:**
1. Veja: [CONFIGURAR_COOKIES_ML.md](CONFIGURAR_COOKIES_ML.md)
2. Atualize cookies no `.env`
3. Reinicie: `docker-compose restart scraper-promo`

---

## 🔄 Comandos Úteis

```bash
# Reiniciar tudo
docker-compose restart

# Parar tudo
docker-compose down

# Ver uso de recursos
docker stats

# Atualizar código
git pull
docker-compose up -d --build

# Backup sessão WhatsApp
docker run --rm -v projeto-2026_whatsapp-session:/data \
  -v $(pwd):/backup alpine \
  tar czf /backup/whatsapp-backup.tar.gz -C /data .
```

---

## 📱 Usar no Celular

Para acessar de qualquer lugar:

### **Opção 1: ngrok (Grátis, temporário)**

```bash
# Instalar ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Criar túnel
ngrok http 80
```

**Resultado:**
```
Forwarding: https://abc123.ngrok.io → http://localhost:80
```

Use: `https://abc123.ngrok.io`

### **Opção 2: Domínio próprio (Profissional)**

1. Comprar domínio (ex: registro.br)
2. Configurar DNS A record: `seudominio.com → SEU_IP`
3. Instalar SSL: `sudo certbot --nginx`

---

## 🎯 Próximos Passos

1. **Monitorar primeiros dias:**
   - Verificar logs diariamente
   - Ajustar intervalos se necessário

2. **Adicionar mais produtos:**
   - Via interface web ou
   - Deixar clonagem automática funcionar

3. **Configurar backup:**
   - Backup semanal da sessão WhatsApp
   - Supabase já faz backup automático

4. **Renovar cookies ML:**
   - Marcar no calendário: renovar a cada 25 dias
   - Veja: [CONFIGURAR_COOKIES_ML.md](CONFIGURAR_COOKIES_ML.md)

---

## 💰 Custos Mensais

### **Setup Básico (Recomendado):**
- VPS Contabo (4GB RAM): €4.99 (~R$ 30/mês)
- Supabase Free Tier: R$ 0
- **Total: ~R$ 30/mês**

### **Setup Profissional:**
- DigitalOcean (2GB RAM): $12 (~R$ 60/mês)
- Domínio .com.br: R$ 40/ano
- SSL Let's Encrypt: Grátis
- **Total: ~R$ 63/mês**

---

## 📚 Documentação Completa

- [CHECKLIST_DEPLOY.md](CHECKLIST_DEPLOY.md) - Checklist completo
- [INSTRUCOES_DEPLOY.md](INSTRUCOES_DEPLOY.md) - Instruções detalhadas
- [CONFIGURAR_COOKIES_ML.md](CONFIGURAR_COOKIES_ML.md) - Renovar cookies ML
- [README.md](README.md) - Visão geral do projeto

---

## 🆘 Precisa de Ajuda?

**Logs completos:**
```bash
docker-compose logs > debug.log
cat debug.log | grep ERROR
```

**Verificar saúde:**
```bash
docker-compose ps
curl http://localhost:3001/status
curl http://localhost/
```

**Reiniciar do zero:**
```bash
docker-compose down -v
rm -rf whatsapp-monitor/auth_info_baileys
docker-compose up -d --build
# Escanear QR Code novamente
```

---

**Deploy feito em:** ___/___/2024
**IP do servidor:** ___.___.___._____
**Status:** 🟢 Online / 🔴 Offline

---

✅ **Sistema configurado e rodando!**

🎓 Projeto Acadêmico - João - CC 2025
