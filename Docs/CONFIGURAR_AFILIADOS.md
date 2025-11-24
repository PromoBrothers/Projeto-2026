# 🔗 Como Configurar Seus Links de Afiliado

## 📝 Passo a Passo

### 1. **Abra o arquivo `.env`** na raiz do projeto

### 2. **Adicione seus IDs de afiliado** (já configurado):

```env
# IDs de Afiliado - Configure com seus próprios IDs
AMAZON_ASSOCIATES_TAG=promobrothers-20
MERCADOLIVRE_AFFILIATE_ID=seu-id-mercadolivre
SHOPEE_AFFILIATE_ID=seu-id-shopee
MAGAZINELUIZA_AFFILIATE_ID=seu-id-magalu
AMERICANAS_AFFILIATE_ID=seu-id-americanas
```

### 3. **Substitua pelos seus IDs reais:**

---

## 🛒 Como Obter Seu ID de Afiliado por Plataforma

### 📦 **AMAZON ASSOCIATES**

1. Acesse: https://associados.amazon.com.br/
2. Faça login ou cadastre-se
3. Vá em **Ferramentas** → **Link do Produto**
4. Seu ID aparece como: `seu-id-20`
5. **Substitua**: `AMAZON_ASSOCIATES_TAG=seu-id-20`

**Exemplo de link gerado:**
```
https://www.amazon.com.br/dp/B0DBKS74P8?tag=seu-id-20
```

---

### 🛒 **MERCADO LIVRE**

1. Acesse: https://developers.mercadolivre.com.br/
2. Cadastre-se no programa de afiliados
3. Obtenha seu **tracking_id** ou **affiliate_id**
4. **Substitua**: `MERCADOLIVRE_AFFILIATE_ID=seu_tracking_id`

**Exemplo de link gerado:**
```
https://www.mercadolivre.com.br/p/MLB123456?tracking_id=seu_tracking_id
```

---

### 🛍️ **SHOPEE**

1. Acesse: https://affiliate.shopee.com.br/
2. Faça cadastro no Programa de Afiliados
3. Obtenha seu **Affiliate ID**
4. **Substitua**: `SHOPEE_AFFILIATE_ID=seu_affiliate_id`

**Exemplo de link gerado:**
```
https://shopee.com.br/product/123456?affi_id=seu_affiliate_id
```

---

### 🏪 **MAGAZINE LUIZA**

1. Acesse: https://afiliados.magazineluiza.com.br/
2. Cadastre-se no programa de afiliados
3. Obtenha seu **partner_id**
4. **Substitua**: `MAGAZINELUIZA_AFFILIATE_ID=seu_partner_id`

---

### 🛒 **AMERICANAS**

1. Acesse: https://afiliados.americanas.com.br/
2. Cadastre-se no programa
3. Obtenha seu **affiliate_id**
4. **Substitua**: `AMERICANAS_AFFILIATE_ID=seu_affiliate_id`

---

## 🔄 Como o Sistema Usa os Links de Afiliado

Quando você faz scraping de um produto, o sistema:

1. ✅ **Detecta** a URL original
2. ✅ **Faz scraping** completo do produto
3. ✅ **Adiciona seu ID de afiliado** automaticamente:
   ```
   https://www.amazon.com.br/dp/B0DBKS74P8?tag=promobrothers-20
   ```
4. ✅ **Salva no banco** com seu link de afiliado
5. ✅ **Quando enviar o webhook**, vai com SEU link!

---

## 📊 Onde o Link de Afiliado é Adicionado

### **No código:**

**1. Amazon Scraper** ([app/amazon_scraping.py](app/amazon_scraping.py)):
```python
def _add_affiliate_tag(self, url: str) -> str:
    affiliate_tag = ScrapingConfig.AFFILIATE_IDS.get('amazon')
    if affiliate_tag and 'tag=' not in url:
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}tag={affiliate_tag}"
    return url
```

**2. Mercado Livre Scraper** ([app/scraping.py](app/scraping.py)):
```python
def _add_affiliate_params(self, url: str) -> str:
    tracking_id = ScrapingConfig.AFFILIATE_IDS.get('mercadolivre')
    if tracking_id:
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}tracking_id={tracking_id}"
    return url
```

---

## 🧪 Como Testar se Está Funcionando

### **Teste 1: Verificar configuração**

```bash
python -c "from app.config import ScrapingConfig; print(ScrapingConfig.AFFILIATE_IDS)"
```

**Resultado esperado:**
```python
{
    'amazon': 'promobrothers-20',
    'mercadolivre': 'seu-id-mercadolivre',
    'shopee': 'seu-id-shopee',
    ...
}
```

### **Teste 2: Ver no dashboard**

1. Acesse: http://localhost:5000/produtos
2. Filtre por "não agendado"
3. Veja o link do produto com seu ID de afiliado

---

## ⚠️ **IMPORTANTE: Reinicie o Flask após alterar o .env**

```bash
# Pare o Flask (Ctrl+C no terminal)
# Inicie novamente:
python run.py
```

Ou use:
```bash
START_FLASK.bat
```

---

## 💰 Comissões por Plataforma

| Plataforma | Comissão Média | Link do Programa |
|------------|---------------|------------------|
| **Amazon** | 1% - 10% | https://associados.amazon.com.br/ |
| **Mercado Livre** | 1% - 8% | https://developers.mercadolivre.com.br/ |
| **Shopee** | 5% - 15% | https://affiliate.shopee.com.br/ |
| **Magazine Luiza** | 3% - 7% | https://afiliados.magazineluiza.com.br/ |
| **Americanas** | 2% - 8% | https://afiliados.americanas.com.br/ |

---

## 🎯 Resumo

1. ✅ Cadastre-se nos programas de afiliados
2. ✅ Obtenha seus IDs/Tags
3. ✅ Configure no `.env`
4. ✅ Reinicie o Flask
5. ✅ Teste fazendo scraping de um produto
6. ✅ Verifique se o link tem seu ID de afiliado

**Pronto! Todos os produtos terão automaticamente SEU link de afiliado!** 🎉

---

## 📞 Suporte

Se tiver dúvidas sobre como obter os IDs de afiliado de alguma plataforma específica, consulte a documentação oficial de cada programa de afiliados.
