# ✅ CHECKLIST COMPLETO PARA DEPLOY EM PRODUÇÃO

## 📋 Status Atual do Projeto

### ✅ **O que JÁ está pronto:**

1. **Código-fonte completo**
   - ✅ Backend Flask implementado
   - ✅ WhatsApp Monitor (Node.js + Baileys)
   - ✅ Sistema de clonagem de links ML
   - ✅ Scrapers (Amazon, ML, Shopee)
   - ✅ Sistema de afiliados
   - ✅ Scheduler de mensagens
   - ✅ Integração Supabase

2. **Docker/Containerização**
   - ✅ Dockerfile principal (Python/Flask)
   - ✅ Dockerfile WhatsApp Monitor (Node.js)
   - ✅ docker-compose.yml configurado
   - ✅ .dockerignore configurado

3. **Documentação**
   - ✅ README.md completo
   - ✅ INSTRUCOES_DEPLOY.md
   - ✅ Múltiplos guias de funcionalidades
   - ✅ Troubleshooting guides

---

## ❌ **O que FALTA para deploy:**

### 1. **Variáveis de Ambiente (.env para produção)**

**Prioridade: 🔴 CRÍTICA**

**O que fazer:**

```bash
# 1. Criar arquivo .env para produção
cp .env.example .env.production

# 2. Preencher TODAS as variáveis obrigatórias:
```

**Variáveis OBRIGATÓRIAS que precisam ser configuradas:**

#### a) **Supabase** (Banco de dados e Storage)
```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_BUCKET_NAME=imagens_melhoradas_tech
```

**Onde obter:**
- Acesse: https://supabase.com/dashboard
- Selecione seu projeto
- Settings → API
- Copie `Project URL` e `service_role key`

#### b) **Mercado Livre - Cookies e CSRF**
```env
ML_CSRF_TOKEN=bKhKU-g6VetNitGbSos7ud5y
ML_COOKIE__CSRF=bKhKU-g6VetNitGbSos7ud5y
ML_COOKIE_ORGNICKP=gabrielvilelaluiz
ML_COOKIE_ORGUSERIDP=404150719
# ... (todos os outros cookies)
```

**Onde obter:**
- Faça login no Mercado Livre
- F12 → Application → Cookies → mercadolivre.com.br
- Copie cada cookie
- **⚠️ IMPORTANTE:** Renovar a cada 30 dias!

**Veja:** [CONFIGURAR_COOKIES_ML.md](CONFIGURAR_COOKIES_ML.md)

#### c) **Amazon Associates (Opcional)**
```env
AMAZON_ASSOCIATES_TAG=promobrothers-20
SCRAPERAPI_KEY=seu-api-key-aqui
```

**Onde obter:**
- Amazon Associates: https://affiliate-program.amazon.com.br/
- ScraperAPI: https://www.scraperapi.com/

#### d) **Autenticação Flask**
```env
# Gerar token seguro:
python -c "import secrets; print(secrets.token_urlsafe(32))"

FLASK_API_TOKEN=token-gerado-aqui
LOGIN_USERNAME=seu-usuario
LOGIN_PASSWORD=sua-senha-forte
```

---

### 2. **Servidor/Hospedagem**

**Prioridade: 🔴 CRÍTICA**

**Opções recomendadas:**

#### **Opção A: VPS (Recomendado para produção)**

**Provedores:**
- **DigitalOcean** (Droplet) - $6/mês (1GB RAM)
- **AWS EC2** - t3.micro (free tier 12 meses)
- **Google Cloud** - e2-micro (free tier)
- **Contabo** - €4.99/mês (4GB RAM) - Melhor custo/benefício

**Requisitos mínimos:**
- 1 CPU core
- 2GB RAM (recomendado 4GB)
- 20GB SSD
- Ubuntu 22.04 LTS

**O que fazer:**
1. Criar conta no provedor
2. Criar droplet/instância
3. Anotar IP público
4. Configurar SSH key

#### **Opção B: PaaS (Mais fácil, mas mais caro)**

**Provedores:**
- **Railway** - $5/mês base
- **Render** - Free tier disponível
- **Heroku** - $7/mês por dyno

**Limitações:**
- WhatsApp pode desconectar com frequência (ambiente efêmero)
- Custo maior em escala

---

### 3. **DNS e Domínio (Opcional)**

**Prioridade: 🟡 MÉDIA**

**Se quiser domínio próprio:**

```bash
# Registrar domínio
# Ex: promobrothers.com.br

# Configurar DNS:
A    @              123.456.789.0  (IP do servidor)
A    www            123.456.789.0
```

**Provedores:**
- Registro.br (domínios .br)
- Namecheap
- Cloudflare (com DNS grátis)

---

### 4. **SSL/HTTPS (Recomendado)**

**Prioridade: 🟡 MÉDIA**

**Usar Nginx + Let's Encrypt:**

```bash
# Instalar Nginx
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx

# Configurar Nginx reverse proxy
sudo nano /etc/nginx/sites-available/promobrothers

# Obter certificado SSL
sudo certbot --nginx -d seudominio.com.br
```

**Configuração Nginx:**
```nginx
server {
    listen 80;
    server_name seudominio.com.br;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /whatsapp {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }
}
```

---

### 5. **Firewall e Segurança**

**Prioridade: 🔴 CRÍTICA**

**Configurar UFW (Ubuntu Firewall):**

```bash
# Habilitar firewall
sudo ufw enable

# Permitir SSH (IMPORTANTE!)
sudo ufw allow 22/tcp

# Permitir HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Permitir WhatsApp Monitor (se necessário acesso externo ao QR)
sudo ufw allow 3001/tcp

# Verificar status
sudo ufw status
```

**Outras medidas:**
- ✅ Mudar porta SSH padrão (22 → outra)
- ✅ Desabilitar login root via SSH
- ✅ Usar SSH keys ao invés de senha
- ✅ Instalar fail2ban (proteção brute-force)

---

### 6. **Monitoramento e Logs**

**Prioridade: 🟢 BAIXA (mas recomendado)**

**Opções:**

#### a) **Logs básicos:**
```bash
# Ver logs do Docker
docker-compose logs -f

# Salvar logs em arquivo
docker-compose logs > logs.txt
```

#### b) **Monitoramento de recursos:**
```bash
# Instalar htop
sudo apt install htop

# Monitorar containers
docker stats
```

#### c) **Alertas (opcional):**
- **Uptime Robot** - Ping a cada 5 min (grátis)
- **Better Uptime** - Alertas via email/SMS
- **Sentry** - Rastreamento de erros (grátis até 5k eventos/mês)

---

### 7. **Backup**

**Prioridade: 🟡 MÉDIA**

**O que fazer backup:**

1. **Banco de dados Supabase:**
   - Supabase já faz backup automático
   - Configure backup manual semanal

2. **Sessão do WhatsApp:**
   ```bash
   # Backup do volume Docker
   docker run --rm -v whatsapp-session:/data -v $(pwd):/backup \
     alpine tar czf /backup/whatsapp-backup.tar.gz -C /data .
   ```

3. **Código-fonte:**
   - ✅ Já está no GitHub
   - Configure deploy automático com GitHub Actions (opcional)

---

## 🚀 PASSO A PASSO PARA DEPLOY

### **Fase 1: Preparação Local (10 min)**

```bash
# 1. Garantir que tudo funciona localmente
docker-compose down
docker-compose up -d --build

# 2. Testar tudo
# - Acessar http://localhost
# - Escanear QR Code
# - Enviar mensagem teste

# 3. Criar .env.production com todas as variáveis
cp .env .env.production
# Editar e preencher todas as variáveis
```

---

### **Fase 2: Configuração do Servidor (30 min)**

```bash
# 1. Conectar ao servidor via SSH
ssh root@SEU_IP

# 2. Atualizar sistema
sudo apt update && sudo apt upgrade -y

# 3. Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 4. Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 5. Instalar Git
sudo apt install git -y

# 6. Clonar repositório
git clone https://github.com/seu-usuario/Projeto-2026.git
cd Projeto-2026
```

---

### **Fase 3: Configuração do Projeto (15 min)**

```bash
# 1. Criar arquivo .env
nano .env
# Colar conteúdo do .env.production
# Salvar: Ctrl+O, Enter, Ctrl+X

# 2. Configurar permissões
chmod 600 .env

# 3. Build das imagens
docker-compose build

# 4. Subir containers
docker-compose up -d

# 5. Verificar status
docker-compose ps
```

---

### **Fase 4: Conectar WhatsApp (5 min)**

```bash
# 1. Acessar QR Code
# http://SEU_IP:3001/qr

# 2. Escanear com WhatsApp

# 3. Verificar conexão
curl http://localhost:3001/status

# Deve retornar: {"connected": true, ...}
```

---

### **Fase 5: Testes Finais (15 min)**

```bash
# 1. Acessar interface web
# http://SEU_IP

# 2. Fazer login

# 3. Adicionar produto teste

# 4. Enviar mensagem manual

# 5. Configurar grupos automáticos

# 6. Testar agendamento

# 7. Verificar logs
docker-compose logs -f scraper-promo
docker-compose logs -f whatsapp-monitor
```

---

## 📊 CHECKLIST FINAL PRÉ-PRODUÇÃO

### **Configuração:**
- [ ] Arquivo .env completo com TODAS as variáveis
- [ ] Cookies ML atualizados (< 30 dias)
- [ ] Supabase configurado e testado
- [ ] Amazon Associates configurado (se usar)

### **Servidor:**
- [ ] VPS/servidor provisionado
- [ ] SSH configurado e testando
- [ ] Docker + Docker Compose instalados
- [ ] Firewall configurado (UFW)
- [ ] Fail2ban instalado (opcional)

### **Aplicação:**
- [ ] Código clonado no servidor
- [ ] Build das imagens Docker bem-sucedido
- [ ] Containers rodando (2/2)
- [ ] Healthchecks passando

### **WhatsApp:**
- [ ] QR Code escaneado
- [ ] Status retorna `connected: true`
- [ ] Teste de envio manual funcionando
- [ ] Grupos configurados

### **Banco de Dados:**
- [ ] Tabelas criadas no Supabase
- [ ] Bucket de imagens criado e público
- [ ] Políticas de acesso configuradas

### **Testes:**
- [ ] Adicionar produto manual
- [ ] Scraping funcionando (Amazon, ML, Shopee)
- [ ] Links de afiliado sendo gerados
- [ ] Mensagens sendo enviadas
- [ ] Agendamento funcionando
- [ ] Clonagem de links /sec/ funcionando

### **Segurança:**
- [ ] Senhas fortes configuradas
- [ ] Tokens seguros gerados
- [ ] Firewall habilitado
- [ ] Portas desnecessárias fechadas

### **Monitoramento:**
- [ ] Uptime Robot configurado (opcional)
- [ ] Logs sendo salvos
- [ ] Alertas configurados (opcional)

### **Backup:**
- [ ] Backup da sessão WhatsApp
- [ ] Código no Git atualizado
- [ ] Supabase com backup automático

---

## ⏱️ ESTIMATIVA DE TEMPO TOTAL

| Fase | Tempo Estimado |
|------|----------------|
| Preparação local | 10 min |
| Configuração servidor | 30 min |
| Setup projeto | 15 min |
| Conectar WhatsApp | 5 min |
| Testes finais | 15 min |
| **TOTAL** | **~75 min (1h15min)** |

---

## 💰 ESTIMATIVA DE CUSTOS MENSAIS

### **Opção Econômica:**
| Item | Custo/mês |
|------|-----------|
| VPS Contabo (4GB RAM) | €4.99 (~R$ 30) |
| Supabase Free Tier | R$ 0 |
| ScraperAPI (opcional) | $0-29 |
| **TOTAL** | **R$ 30-180** |

### **Opção Profissional:**
| Item | Custo/mês |
|------|-----------|
| DigitalOcean Droplet (2GB) | $12 (~R$ 60) |
| Domínio .com.br | R$ 40/ano (~R$ 3/mês) |
| SSL Let's Encrypt | R$ 0 |
| Supabase Pro | $25 (~R$ 125) |
| ScraperAPI Pro | $49 (~R$ 245) |
| **TOTAL** | **R$ 433/mês** |

---

## 🆘 SUPORTE E TROUBLESHOOTING

### **Erros comuns no deploy:**

1. **"Port 80 already in use"**
   ```bash
   # Verificar o que está usando a porta
   sudo lsof -i :80
   # Parar serviço (geralmente Apache/Nginx)
   sudo systemctl stop apache2
   ```

2. **"WhatsApp não conecta"**
   - Verificar logs: `docker-compose logs whatsapp-monitor`
   - Limpar sessão: `docker-compose down -v`
   - Escanear QR novamente

3. **"Erro ao gerar link ML"**
   - Verificar cookies no .env
   - Renovar cookies (veja CONFIGURAR_COOKIES_ML.md)
   - Verificar logs: `docker-compose logs scraper-promo | grep ML`

4. **"Out of memory"**
   - Aumentar RAM do servidor (mínimo 2GB)
   - Limitar recursos Docker no docker-compose.yml

---

## 📚 DOCUMENTAÇÃO ADICIONAL

- [INSTRUCOES_DEPLOY.md](INSTRUCOES_DEPLOY.md) - Instruções detalhadas
- [CONFIGURAR_COOKIES_ML.md](CONFIGURAR_COOKIES_ML.md) - Como renovar cookies ML
- [FEATURE_CLONAGEM_ETICA_ML.md](FEATURE_CLONAGEM_ETICA_ML.md) - Sistema de clonagem
- [README.md](README.md) - Visão geral do projeto

---

## ✅ PRÓXIMOS PASSOS

Após deploy bem-sucedido:

1. **Monitoramento:**
   - Configurar Uptime Robot
   - Verificar logs diariamente (primeiros 7 dias)

2. **Otimização:**
   - Ajustar intervalos de agendamento
   - Configurar cache (se necessário)
   - Otimizar scrapers

3. **Escala:**
   - Adicionar mais grupos
   - Configurar múltiplos afiliados
   - Implementar analytics

4. **Manutenção:**
   - Renovar cookies ML mensalmente
   - Atualizar dependências
   - Backup semanal da sessão WhatsApp

---

**Última atualização:** 24/11/2024
**Versão:** 1.0
**Desenvolvido por:** João - Projeto Acadêmico CC 2025
