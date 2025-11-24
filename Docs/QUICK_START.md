# 🚀 Quick Start - Promo Brothers Scraper v2

Guia rápido de instalação e uso do sistema completo.

## 📦 O que tem neste projeto?

1. **Web Scraper** - Scraping de Amazon, Mercado Livre e Shopee
2. **Sistema de Fila** - Processamento em massa de produtos
3. **API REST** - Interface completa para todas as funcionalidades
4. **Dashboard** - Interface web para gerenciar produtos

---

## ⚡ Instalação Rápida

### 1. Clonar repositório (se ainda não fez)

```bash
git clone <seu-repo>
cd Promo-brothers-Scraper-v2
```

### 2. Instalar Python (Python 3.8+)

Baixe de: https://python.org

### 3. Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

```bash
# Copiar exemplo
cp .env.example .env

# Editar com suas credenciais
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Mínimo necessário:**
- `SUPABASE_URL` - URL do seu projeto Supabase
- `SUPABASE_KEY` - Chave do Supabase
- `WEBHOOK_URL` - URL do seu webhook (ex: n8n, Make.com)

### 5. Iniciar Flask API

```bash
python run.py
```

Deve aparecer:
```
Flask app created successfully!
Starting server on 0.0.0.0:5000
```

---

## 🎯 Funcionalidades Básicas

### Testar API

```bash
curl http://localhost:5000/teste
```

### Fazer Scraping de Produto

```bash
curl -X POST http://localhost:5000/webhook/processar \
  -H "Content-Type: application/json" \
  -d '{
    "url_produto": "https://amazon.com.br/dp/SEU_PRODUTO",
    "afiliado_link": "seu-link-afiliado"
  }'
```

### Buscar Produtos

```bash
# Mercado Livre
curl -X POST http://localhost:5000/buscar \
  -H "Content-Type: application/json" \
  -d '{"produto": "notebook", "max_pages": 2}'

# Amazon
curl -X POST http://localhost:5000/buscar-amazon \
  -H "Content-Type: application/json" \
  -d '{"produto": "fone bluetooth", "max_pages": 2}'
```

---

## 📚 Documentação Completa

- **API Endpoints:** Ver documentação da API
- **Configuração de Afiliados:** Ver [CONFIGURAR_AFILIADOS.md](CONFIGURAR_AFILIADOS.md)
- **Supabase:** Ver [INSTRUCOES_SUPABASE.md](INSTRUCOES_SUPABASE.md)

---

## 🔍 Verificação de Instalação

### Checklist

- [ ] Flask rodando na porta 5000
- [ ] Supabase configurado
- [ ] Webhook URL configurado

### Comandos de Teste

```bash
# Testar Flask
curl http://localhost:5000/teste

# Testar scraping
curl -X POST http://localhost:5000/webhook/processar \
  -H "Content-Type: application/json" \
  -d '{
    "url_produto": "https://amazon.com.br/dp/SEU_PRODUTO",
    "afiliado_link": "seu-link-afiliado"
  }'
```

---

## 🚨 Problemas Comuns

### Porta 5000 já em uso

**Windows:**
```bash
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -i :5000
kill -9 <PID>
```

---

## 🎓 Próximos Passos

1. ✅ Instalar e testar sistema básico
2. 🔧 Configurar links de afiliados
3. 📖 Ler documentação completa
4. 🚀 Colocar em produção

---

## 📞 Suporte

Se tiver problemas:
1. Verifique os logs
2. Revise a documentação
3. Verifique issues no GitHub

---

**Desenvolvido para Promo Brothers** 🚀

Sistema completo de scraping e clonagem de produtos v2.0
