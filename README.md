# 🛒 Sistema Automatizado de Scraping e Divulgação de Promoções

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-brightgreen.svg)](https://nodejs.org/)

Sistema completo de automação para scraping, processamento e divulgação de promoções em marketplaces brasileiros com integração WhatsApp.

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Requisitos](#-requisitos)
- [Instalação Rápida](#-instalação-rápida)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [API Endpoints](#-api-endpoints)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Visão Geral

Este projeto é um **sistema completo de automação** desenvolvido como projeto acadêmico que:

1. **Realiza scraping** de produtos em marketplaces (Amazon, Mercado Livre, Shopee)
2. **Gera automaticamente links de afiliado** com estratégias inteligentes de fallback
3. **Armazena dados** em banco Supabase (PostgreSQL) com imagens otimizadas
4. **Integra com WhatsApp** via Baileys para divulgação automatizada
5. **Agenda envios** inteligentes para grupos WhatsApp
6. **Oferece interface web** responsiva para gerenciamento completo

---

## ✨ Funcionalidades

### 🔍 Web Scraping Inteligente
- ✅ Suporte a múltiplos marketplaces (Amazon, ML, Shopee)
- ✅ Anti-bot bypass com proxies e User-Agents rotativos
- ✅ Extração automática de: título, preço, imagem, cupons
- ✅ Cache inteligente para otimização

### 💰 Sistema de Afiliados
- ✅ **Amazon**: Integração oficial Amazon Associates
- ✅ **Mercado Livre**: Sistema proprietário com cookies
  - 4 estratégias de fallback automáticas
  - Otimização de 40s → 1s na geração
  - Cache de falhas para performance

### 📱 Integração WhatsApp
- ✅ Conexão via Baileys (biblioteca oficial)
- ✅ Envio manual ou agendado
- ✅ Interface modal para seleção de grupos
- ✅ Suporte a imagens e textos
- ✅ QR Code para autenticação

### 🎛️ Painel de Controle Web
- ✅ Interface responsiva e intuitiva
- ✅ Gerenciamento completo de produtos
- ✅ Sistema de abas (Pendentes/Agendados/Enviados)
- ✅ Agendamento de envios
- ✅ Histórico de mensagens

---

## 🛠️ Tecnologias

**Backend:** Python 3.11+, Flask 2.3+, BeautifulSoup4, Supabase
**WhatsApp:** Node.js 18+, Baileys 6.7+, Express.js
**Frontend:** HTML5, CSS3, JavaScript
**Database:** Supabase (PostgreSQL + S3 Storage)

---

## 📦 Requisitos

- **Python** 3.11 ou superior
- **Node.js** 18 ou superior
- Conta **Supabase** (gratuita disponível)
- Conta **Mercado Livre** com programa de afiliados
- **Amazon Associates** (opcional)

---

## 🚀 Instalação Rápida

### 1. Clone e Configure Python

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/scraper-promo.git
cd scraper-promo

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual (Windows)
.venv\Scripts\activate
# Ou Linux/Mac
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configure WhatsApp Monitor

```bash
cd whatsapp-monitor
npm install
cd ..
```

### 3. Configure Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas credenciais
# IMPORTANTE: Preencha TODAS as variáveis necessárias
```

**Consulte a seção [Configuração](#-configuração) para detalhes sobre cada variável.**

---

## ⚙️ Configuração

### 1. Supabase

1. Crie uma conta em [supabase.com](https://supabase.com)
2. Crie um novo projeto
3. Vá em **Settings** → **API** e copie:
   - `Project URL` → `SUPABASE_URL`
   - `service_role key` → `SUPABASE_KEY`

4. Execute este SQL para criar a tabela:

```sql
CREATE TABLE promocoes (
    id TEXT PRIMARY KEY,
    titulo TEXT,
    link_produto TEXT,
    preco_atual TEXT,
    preco_com_cupom TEXT,
    imagem_url TEXT,
    marketplace TEXT,
    cupom TEXT,
    status TEXT DEFAULT 'pendente',
    data_agendamento TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

5. Crie um bucket para imagens:
   - **Storage** → **New Bucket**
   - Nome: `imagens_melhoradas_tech`
   - Público: **Sim**

### 2. Mercado Livre (IMPORTANTE!)

O ML requer cookies de sessão do navegador:

1. Faça login no [Mercado Livre](https://www.mercadolivre.com.br/)
2. Abra **DevTools** (F12)
3. **Application** → **Cookies** → `https://www.mercadolivre.com.br`
4. Copie os valores dos cookies para o `.env`:
   - `_csrf` → `ML_COOKIE__CSRF` e `ML_CSRF_TOKEN`
   - `orgnickp` → `ML_COOKIE_ORGNICKP`
   - `orguseridp` → `ML_COOKIE_ORGUSERIDP`
   - E todos os outros listados no `.env.example`

**⚠️ IMPORTANTE**: Os cookies expiram após ~30 dias.

### 3. Amazon Associates (Opcional)

1. Inscreva-se em [affiliate-program.amazon.com.br](https://affiliate-program.amazon.com.br/)
2. Obtenha seu **Associate Tag**
3. Adicione em `.env`: `AMAZON_ASSOCIATES_TAG=seu-tag-20`

---

## 🎮 Uso

### Iniciar o Sistema

**Terminal 1 - Flask:**
```bash
.venv\Scripts\activate  # Windows
# ou: source .venv/bin/activate  # Linux/Mac

python run.py
```

**Terminal 2 - WhatsApp Monitor:**
```bash
cd whatsapp-monitor
npm start
```

### Conectar WhatsApp

1. Acesse: `http://localhost:3001/qr`
2. Escaneie o QR Code com WhatsApp
3. Aguarde: "Conectado ao WhatsApp com sucesso!"

### Acessar Interface

Abra: `http://localhost:5000`

### Usar o Sistema

1. **Adicionar Produto**: Cole URL do marketplace
2. **Enviar Manual**: Clique "📤 Enviar Agora" → Selecione grupos
3. **Agendar**: Clique "📅 Agendar" → Escolha data/hora e grupos

---

## 📁 Estrutura do Projeto

```
scraper-promo/
├── app/                     # Aplicação Flask
│   ├── routes.py            # API endpoints
│   ├── database.py          # Supabase integration
│   ├── scraping.py          # Scraping logic
│   ├── ml_affiliate.py      # ML affiliate system
│   ├── scheduler.py         # Message scheduler
│   ├── static/              # Frontend assets
│   └── templates/           # HTML templates
│
├── whatsapp-monitor/        # WhatsApp server (Node.js)
│   ├── server.js            # Express + Baileys
│   └── package.json         # Dependencies
│
├── .env                     # Environment variables (gitignored)
├── .env.example             # Template
├── requirements.txt         # Python dependencies
├── run.py                   # Entry point
└── README.md                # This file
```

---

## 🔌 API Endpoints

### Produtos

- `POST /adicionar-produto` - Adiciona produto via scraping
- `GET /produtos` - Lista produtos (query: `status`, `order`, `page`)
- `GET /produtos/<id>` - Detalhes de produto
- `DELETE /produtos/<id>` - Remove produto

### WhatsApp

- `POST /enviar-mensagem` - Envia mensagem manual
- `GET /whatsapp/groups` - Lista grupos disponíveis
- `GET /whatsapp/status` - Status da conexão

### Scheduler

- `GET /scheduler/status` - Status do agendador
- `POST /configurar-grupos-auto` - Configura envio automático

---

## 🐛 Troubleshooting

### WhatsApp não conecta

**Erro:** `{"error":"No sessions"}`

**Solução:**
```bash
# Parar WhatsApp Monitor (Ctrl+C)
cd whatsapp-monitor
powershell -Command "Remove-Item -Recurse -Force auth_info_baileys"
npm start
# Escanear novo QR Code
```

### Link de afiliado ML não gera

**Solução:**
1. Verifique se TODOS os cookies estão no `.env`
2. Renove os cookies (eles expiram)
3. Verifique o `MERCADOLIVRE_AFFILIATE_ID`

### Modal não abre

**Solução:**
1. Limpe cache do navegador (Ctrl+Shift+R)
2. Verifique console (F12) para erros
3. Confirme que Flask está rodando

### Mais problemas?

Consulte:
- [RESOLVER_NO_SESSIONS.md](RESOLVER_NO_SESSIONS.md)
- [DIAGNOSTICO_MODAL.md](DIAGNOSTICO_MODAL.md)
- [Logs do Flask/WhatsApp Monitor](#)

---

## 📚 Documentação Completa

- **[RELATORIO_ACADEMICO.md](RELATORIO_ACADEMICO.md)** - Relatório acadêmico completo
- **[SISTEMA_ENVIO_MENSAGENS.md](SISTEMA_ENVIO_MENSAGENS.md)** - Sistema de mensagens
- **[ATUALIZADO_BAILEYS.md](ATUALIZADO_BAILEYS.md)** - Atualização do Baileys

---

## 🙏 Agradecimentos

- **Claude Code** - Desenvolvimento e debugging
- **Baileys** - WhatsApp Web API
- **Supabase** - Backend as a Service
- **Comunidade Open Source**

---

## 📞 Contato

**Desenvolvido por:** João
**Instituição:** Centro Universitário
**Curso:** Ciência da Computação
**Ano:** 2025

---

## ⚠️ Aviso Legal

Este projeto é para fins educacionais e acadêmicos. O uso de web scraping deve respeitar os termos de serviço dos sites alvos. O desenvolvedor não se responsabiliza pelo uso indevido desta ferramenta.

---

**⭐ Projeto Acadêmico - Janeiro 2025**
