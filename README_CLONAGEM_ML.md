# 🔄 Clonagem Ética de Links ML - Guia Rápido

## 🎯 O que faz?

Quando alguém compartilha um link de afiliado do Mercado Livre no formato:
```
https://mercadolivre.com/sec/1citUM9
```

O sistema **automaticamente**:

1. ✅ **Visita o link** (gerando comissão para o criador)
2. ✅ **Extrai o produto real** da página social
3. ✅ **Cria seu link de afiliado**
4. ✅ **Substitui na mensagem**
5. ✅ **Agenda o reenvio**

---

## 🚀 Como Usar

### Opção 1: Automático (Recomendado)

O sistema detecta automaticamente! Basta:

1. Adicionar o grupo ao monitoramento no WhatsApp Monitor
2. Quando alguém postar um link `/sec/...`, o sistema clona automaticamente

### Opção 2: Manual

1. Abra a interface web: `http://localhost:5000/clone`
2. Cole a mensagem com o link `/sec/...`
3. Clique em "Clonar e Agendar"

---

## 📋 Pré-requisitos

**✅ Tudo já está configurado!**

Apenas certifique-se de que o `.env` tem:

```env
MERCADOLIVRE_AFFILIATE_ID=gabrielvilelaluiz  # Seu ID de afiliado
ML_COOKIE__CSRF=...                          # Cookies atualizados
ML_CSRF_TOKEN=...                            # Token CSRF
```

---

## 🧪 Testar Agora

### Teste Rápido

```bash
# Opção 1: Duplo clique
testar_expandir_link.bat

# Opção 2: Linha de comando
.venv\Scripts\python.exe test_expandir_link_ml.py
```

### Teste Real

1. Inicie Flask: `START_FLASK.bat`
2. Inicie WhatsApp: `START_WHATSAPP.bat`
3. Poste em um grupo monitorado:
   ```
   🔥 Produto TOP!
   https://mercadolivre.com/sec/1citUM9
   ```
4. Veja a mágica acontecer nos logs! ✨

---

## 📊 Exemplo Visual

### Antes
```
┌────────────────────────────────────────┐
│ Mensagem original (de outro afiliado) │
├────────────────────────────────────────┤
│ 🔥 Oferta TOP!                         │
│                                        │
│ https://mercadolivre.com/sec/1citUM9   │
│ (link de afiliado de outra pessoa)    │
└────────────────────────────────────────┘
```

### Processamento
```
⬇️  Sistema acessa o link
⬇️  Extrai produto: /p/MLB123456789
⬇️  Gera SEU link: /sec/ABC123XYZ
```

### Depois
```
┌────────────────────────────────────────┐
│ Mensagem clonada (com SEU afiliado)   │
├────────────────────────────────────────┤
│ 🔥 Oferta TOP!                         │
│                                        │
│ https://mercadolivre.com/sec/ABC123XYZ │
│ (SEU link de afiliado!)                │
└────────────────────────────────────────┘
```

---

## 💰 Vantagens

| Vantagem | Descrição |
|----------|-----------|
| 🤝 **Ético** | Criador original recebe comissão pelo clique |
| ⚡ **Rápido** | Processamento em ~2-3 segundos |
| 🔄 **Automático** | Sem intervenção manual necessária |
| 📊 **Rastreado** | Todos os logs salvos automaticamente |
| 💪 **Robusto** | Múltiplos seletores de fallback |

---

## ⚙️ Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| [app/ml_affiliate.py](app/ml_affiliate.py) | Função `expandir_link_curto_ml()` |
| [app/routes.py](app/routes.py) | Integração em `substituir_links_afiliado()` |
| [test_expandir_link_ml.py](test_expandir_link_ml.py) | Script de teste |
| [FEATURE_CLONAGEM_ETICA_ML.md](FEATURE_CLONAGEM_ETICA_ML.md) | Documentação completa |

---

## 🐛 Problemas?

### Link não expande?

**Verifique:**
1. Link ainda válido no navegador?
2. Cookies ML atualizados? → `CONFIGURAR_COOKIES_ML.md`
3. Internet funcionando?

**Logs úteis:**
```bash
# Veja o que aconteceu
type scraping.log | findstr "Expandindo"
```

### API do ML falha?

**Solução:**
```bash
# Renove os cookies
# Veja: CONFIGURAR_COOKIES_ML.md
```

---

## 📞 Suporte

**Documentação completa:** [FEATURE_CLONAGEM_ETICA_ML.md](FEATURE_CLONAGEM_ETICA_ML.md)

**Logs do sistema:** `scraping.log`

---

✅ **Implementado com sucesso em 24/11/2024**

🎓 Projeto Acadêmico - João - Ciência da Computação 2025
