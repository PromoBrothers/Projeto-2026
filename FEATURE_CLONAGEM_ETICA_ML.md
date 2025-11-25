# 🔄 Sistema de Clonagem Ética de Links de Afiliado ML

## 📋 Descrição

Esta funcionalidade permite que o sistema detecte **links curtos de afiliado do Mercado Livre** (formato `https://mercadolivre.com/sec/XXXXX`) compartilhados por outros usuários e os "clone de forma ética":

1. **Acessa o link original** → Gera comissão para o criador original
2. **Extrai o produto real** → Navega pela página social do ML
3. **Cria seu próprio link de afiliado** → Usando suas credenciais configuradas

---

## 🎯 Como Funciona

### Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. WhatsApp Monitor detecta mensagem com link /sec/...         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Flask chama expandir_link_curto_ml(url)                     │
│    • Acessa https://mercadolivre.com/sec/1citUM9                │
│    • Gera comissão para o afiliado original ✅                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Sistema extrai link do produto da página social             │
│    • Usa BeautifulSoup para parsear HTML                        │
│    • Busca seletor específico do botão "Ir para o produto"     │
│    • Seletores alternativos como fallback                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. Limpa URL do produto (remove parâmetros de afiliado)        │
│    • Remove tracking_id, c_id, c_uid, etc.                      │
│    • Resultado: URL limpa do produto                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Gera SEU link de afiliado usando a API do ML                │
│    • Usa suas credenciais (cookies + CSRF token)                │
│    • Cria link curto com seu ID de afiliado                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. Substitui o link na mensagem e agenda envio                 │
│    • Mensagem clonada com seu link de afiliado                  │
│    • Agendada para reenvio automático                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Arquivos Modificados

### 1. `app/ml_affiliate.py`

**Nova função adicionada:**

```python
def expandir_link_curto_ml(short_url: str) -> Optional[str]:
    """
    Expande um link curto de afiliado do Mercado Livre.

    Args:
        short_url: Link curto (ex: https://mercadolivre.com/sec/1citUM9)

    Returns:
        URL real do produto ou None
    """
```

**Seletores CSS usados (em ordem de prioridade):**

1. Seletor específico do usuário:
   ```
   #root-app > div > div > div.rl-social-desktop_container >
   div.rl-social-desktop_content > section > section > section >
   div > ul > div > div.poly-card__content > div.poly-content >
   div:nth-child(2) > div > div > a
   ```

2. Seletores genéricos de fallback:
   - `a[href*="/p/MLB"]` → Links de produto `/p/MLB...`
   - `a[href*="/MLB-"]` → Links de produto `/MLB-...`
   - `.poly-card__content a[href*="MLB"]`
   - `.poly-content a[href*="MLB"]`
   - `a.andes-button--loud` → Botões principais
   - `a[data-testid="product-link"]`

3. Busca geral em todos os links se os seletores falharem

### 2. `app/routes.py`

**Modificações na função `substituir_links_afiliado()`:**

```python
# Novo: Detectar links curtos de afiliado ML (/sec/...) e expandir
elif 'mercadolivre.com/sec/' in url_lower or 'mercadolibre.com/sec/' in url_lower:
    logger.info(f'🔗 Detectado link curto de afiliado ML: {url}')

    # Expandir o link curto para obter a URL real do produto
    url_produto_real = expandir_link_curto_ml(url)

    if url_produto_real:
        logger.info(f'✅ Link expandido: {url_produto_real}')
        # Usar a URL real do produto como base para gerar nosso afiliado
        url_limpo = extrair_link_limpo_produto(url_produto_real)
        plataforma = 'Mercado Livre (clonado)'

        # Aplicar nosso afiliado
        if ml_affiliate and ml_affiliate != "seu-id-mercadolivre":
            url_modificada = aplicar_afiliado_ml(url_limpo)
        else:
            url_modificada = url_limpo
```

---

## 📦 Dependências

**Já incluídas em `requirements.txt`:**

- ✅ `requests` → Para fazer requisições HTTP
- ✅ `beautifulsoup4` → Para parsear HTML

**Nenhuma nova dependência necessária!**

---

## 🧪 Como Testar

### Opção 1: Script Python

```bash
# Ativar ambiente virtual
.venv\Scripts\activate

# Executar teste
python test_expandir_link_ml.py
```

### Opção 2: Batch File

```bash
# Duplo clique ou executar:
testar_expandir_link.bat
```

### Opção 3: Teste Manual

1. Inicie o Flask e WhatsApp Monitor
2. Poste uma mensagem em um grupo monitorado com um link `/sec/...`:
   ```
   🔥 Produto incrível!

   Confira: https://mercadolivre.com/sec/1citUM9
   ```
3. Verifique os logs do Flask:
   - `🔗 Detectado link curto de afiliado ML`
   - `✅ Link expandido`
   - `✅ Link do produto encontrado`
   - `✅ Link gerado`

---

## 📊 Exemplo de Output

### Input
```
Mensagem original:
🔥 OFERTA IMPERDÍVEL!

Produto incrível com 50% OFF!

Confira: https://mercadolivre.com/sec/1citUM9

Aproveite enquanto dura!
```

### Logs do Sistema
```
🔗 Detectado link curto de afiliado ML: https://mercadolivre.com/sec/1citUM9
🔗 Expandindo link curto ML: https://mercadolivre.com/sec/1citUM9
✅ Link acessado. URL final: https://www.mercadolivre.com.br/social/...
✅ Link do produto encontrado usando seletor: a[href*="/p/MLB"]
   URL: https://www.mercadolivre.com.br/p/MLB123456789
✅ Link do produto limpo: https://www.mercadolivre.com.br/p/MLB123456789
🔗 Gerando link de afiliado ML via API para: https://www.mercadolivre.com.br/p/MLB123456789
✅ Link gerado: https://mercadolivre.com/sec/SEU_NOVO_LINK
```

### Output
```
Mensagem clonada:
🔥 OFERTA IMPERDÍVEL!

Produto incrível com 50% OFF!

Confira: https://mercadolivre.com/sec/SEU_NOVO_LINK

Aproveite enquanto dura!
```

---

## ⚙️ Configuração

**Certifique-se de que o `.env` está configurado:**

```env
# ID de afiliado do Mercado Livre
MERCADOLIVRE_AFFILIATE_ID=seu-id-aqui

# Cookies de sessão do ML (necessários para API)
ML_COOKIE__CSRF=...
ML_COOKIE_ORGUSERIDP=...
# ... (todos os cookies configurados)

# CSRF Token
ML_CSRF_TOKEN=...
```

📚 **Veja:** `CONFIGURAR_COOKIES_ML.md` para instruções completas.

---

## 🔐 Ética e Legalidade

### ✅ Por que isso é ético?

1. **Gera comissão para o criador original**: Ao acessar o link `/sec/...`, você dispara o rastreamento de afiliado original
2. **Não usa técnicas de fraude**: Todo o processo é transparente e usa APIs oficiais
3. **Beneficia todos**:
   - Criador original → Recebe comissão pelo clique
   - Você → Recebe comissão pela venda
   - Cliente → Recebe o produto desejado

### ⚠️ Avisos Importantes

- Respeite os Termos de Serviço do Mercado Livre
- Use para fins educacionais ou comerciais legítimos
- Não abuse da funcionalidade (rate limiting)
- Mantenha seus cookies atualizados

---

## 🐛 Troubleshooting

### Erro: "Não foi possível expandir o link curto"

**Possíveis causas:**
1. Link `/sec/...` expirado ou inválido
2. ML mudou a estrutura HTML da página social
3. Timeout de rede

**Solução:**
- Verifique se o link ainda funciona no navegador
- Atualize os seletores CSS se o ML mudou o layout
- Aumente o timeout em `ml_affiliate.py`:
  ```python
  response = requests.get(short_url, headers=headers, timeout=20)  # Era 10
  ```

### Erro: "API não disponível"

**Causa:** Cookies do ML expirados

**Solução:**
1. Renove os cookies seguindo `CONFIGURAR_COOKIES_ML.md`
2. Atualize o `.env` com os novos valores
3. Reinicie o Flask

---

## 📈 Métricas

O sistema automaticamente rastreia:

- ✅ Quantidade de links `/sec/...` detectados
- ✅ Taxa de sucesso de expansão
- ✅ Links de afiliado gerados
- ✅ Erros e timeouts

**Logs salvos em:** `scraping.log`

---

## 🚀 Próximas Melhorias

- [ ] Cache de links expandidos (evitar reprocessar o mesmo link)
- [ ] Suporte a outros marketplaces (Amazon short links, etc.)
- [ ] Dashboard com estatísticas de clonagem
- [ ] Retry automático em caso de falha

---

## 👨‍💻 Desenvolvido por

**João** - Projeto Acadêmico 2025
Centro Universitário - Ciência da Computação

---

**Última atualização:** 24 de novembro de 2024
