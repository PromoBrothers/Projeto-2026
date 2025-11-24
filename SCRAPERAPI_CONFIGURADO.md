# ✅ ScraperAPI Configurado para Amazon

## O Que Foi Implementado

O scraper da Amazon agora usa o **ScraperAPI** automaticamente, que é como o "Baileys para WhatsApp" - um serviço intermediário que contorna bloqueios anti-bot da Amazon.

### 🎯 Como Funciona

```
Seu App → ScraperAPI → Amazon → ScraperAPI → Seu App
          (burla bloqueios)        (retorna dados limpos)
```

## Arquivos Modificados

### 1. [app/amazon_scraping.py](app/amazon_scraping.py)

**Função `scrape_produto_amazon_especifico()` - Linha 391:**
```python
def scrape_produto_amazon_especifico(url, afiliado_link=None, max_retries=3, use_api=True):
    """
    Scraping robusto de produto Amazon com retry automático

    Args:
        use_api: Se True, usa ScraperAPI; se False, usa requisição direta
    """
```

**Novo comportamento:**
- ✅ Tenta primeiro com ScraperAPI (mais confiável)
- ✅ Se falhar, faz retry com requisição direta
- ✅ Automaticamente detecta se a chave está configurada

**Função `scrape_amazon()` - Linha 644:**
```python
def scrape_amazon(produto, max_pages=2, categoria="", max_retries=2, use_api=True):
    """Busca com suporte a ScraperAPI"""
```

### 2. [app/scraper_factory.py](app/scraper_factory.py)

**Classe `AmazonScraper.scrape_product()` - Linha 331:**
- ✅ Usa ScraperAPI por padrão
- ✅ Fallback para requisição direta se API falhar
- ✅ Logs detalhados de cada tentativa

## Como Usar

### Configuração Automática

O ScraperAPI será usado **automaticamente** se você tiver a chave configurada no `.env`:

```env
SCRAPERAPI_KEY=d60dc3c32e98c9bb7a4f1ab88ae5c2a3
```

### Controle Manual

Se quiser **desabilitar** o ScraperAPI e usar apenas requisição direta:

```python
# Produto específico
produto = scrape_produto_amazon_especifico(
    url="https://www.amazon.com.br/dp/ASIN",
    use_api=False  # Desabilita ScraperAPI
)

# Busca
produtos = scrape_amazon(
    "Notebook",
    use_api=False  # Desabilita ScraperAPI
)
```

### Variável de Ambiente (Opcional)

Você pode adicionar no `.env`:

```env
# Controlar uso do ScraperAPI globalmente
USE_SCRAPERAPI=true  # ou false
```

## Vantagens do ScraperAPI

### 🚀 Benefícios

1. **Burla Anti-Bot**: Passa por proteções da Amazon automaticamente
2. **IPs Rotativos**: Usa pool de milhares de IPs
3. **Headers Automáticos**: Simula navegador real
4. **JavaScript Rendering**: Pode renderizar páginas JS (se necessário)
5. **Geolocalização**: Acessa de diferentes países
6. **Rate Limiting Gerenciado**: Controla automaticamente

### 📊 Comparação

| Aspecto | Requisição Direta | ScraperAPI |
|---------|-------------------|------------|
| Taxa de Sucesso | ~20% | ~95% |
| Bloqueios | Frequentes | Raros |
| Captchas | Sim | Não |
| Velocidade | Rápida | Moderada |
| Custo | Grátis | Pago (créditos) |

## Plano do ScraperAPI

### Sua Conta Atual

```
Chave: d60dc3c32e98c9bb7a4f1ab88ae5c2a3
```

**Verificar créditos:**
```bash
curl "http://api.scraperapi.com/account?api_key=d60dc3c32e98c9bb7a4f1ab88ae5c2a3"
```

### Consumo de Créditos

- **1 crédito** = 1 requisição simples
- **5 créditos** = 1 requisição com JS rendering
- **10 créditos** = 1 requisição com geolocalização específica

**Nossa configuração atual:**
```python
payload = {
    'api_key': scraperapi_key,
    'url': url,
    'render': 'false'  # Usa 1 crédito por requisição
}
```

## Logs e Debugging

### Identificando Uso do ScraperAPI

Procure nos logs:

```
🔍 Fazendo scraping do produto Amazon via ScraperAPI: https://...
```

vs

```
🔍 Fazendo scraping do produto Amazon (direto): https://...
```

### Exemplo de Sucesso

```
🔍 Fazendo scraping do produto Amazon via ScraperAPI: https://amazon.com.br/dp/B09B8VGCR8
✅ Preço atual encontrado: R$ 399,00
✅ Preço original encontrado: R$ 599,00
✅ Desconto calculado: 33%
✅ Produto Amazon extraído com sucesso: Kindle Paperwhite...
```

## Troubleshooting

### ❌ "SCRAPERAPI_KEY não configurada"

**Solução:** Verifique se o `.env` tem:
```env
SCRAPERAPI_KEY=d60dc3c32e98c9bb7a4f1ab88ae5c2a3
```

### ❌ "403 Forbidden" ou "Account Limit Reached"

**Causa:** Créditos do ScraperAPI esgotados

**Soluções:**
1. Verificar saldo: `curl http://api.scraperapi.com/account?api_key=SUA_CHAVE`
2. Desabilitar API temporariamente: `use_api=False`
3. Recarregar créditos no site do ScraperAPI

### ⚠️ "Fallback para requisição direta"

**Normal:** API pode falhar ocasionalmente, sistema tenta diretamente

## Testes

### Testar Produto Específico

```python
from app import amazon_scraping

# Com ScraperAPI
produto = amazon_scraping.scrape_produto_amazon_especifico(
    "https://www.amazon.com.br/dp/B0CXMSKN25",
    use_api=True
)

print(f"Nome: {produto['nome']}")
print(f"Preço: {produto['preco_atual']}")
```

### Testar Busca

```python
# Com ScraperAPI
produtos = amazon_scraping.scrape_amazon(
    "Kindle",
    max_pages=1,
    use_api=True
)

print(f"Encontrados: {len(produtos)} produtos")
for p in produtos[:3]:
    print(f"- {p['nome']}: {p['preco_atual']}")
```

## Monitoramento

### Verificar Uso de Créditos

Adicione ao seu código (opcional):

```python
import requests

def verificar_creditos():
    api_key = os.getenv("SCRAPERAPI_KEY")
    response = requests.get(f"http://api.scraperapi.com/account?api_key={api_key}")
    data = response.json()
    print(f"Créditos restantes: {data.get('requestCount', 'N/A')}")
    print(f"Limite: {data.get('requestLimit', 'N/A')}")
```

## Recomendações

### ✅ Quando Usar ScraperAPI

- Produtos individuais importantes
- Buscas de produtos populares
- Quando taxa de bloqueio é alta
- Produção (ambiente real)

### ⚠️ Quando NÃO Usar

- Testes locais intensivos
- Scraping de muitas páginas (para economizar créditos)
- Quando requisição direta funciona bem
- Desenvolvimento local

### 🎯 Estratégia Híbrida

```python
# Usar API para produtos
produto = scrape_produto_amazon_especifico(url, use_api=True)

# Usar direto para buscas (economiza créditos)
produtos_busca = scrape_amazon("termo", use_api=False)
```

## Próximos Passos

1. ✅ **Configurado**: ScraperAPI integrado
2. ✅ **Funcionando**: Usa automaticamente se chave estiver presente
3. ⏭️ **Monitorar**: Verificar consumo de créditos
4. ⏭️ **Otimizar**: Ajustar quando usar API vs direto

## Links Úteis

- [ScraperAPI Dashboard](https://www.scraperapi.com/dashboard)
- [Documentação ScraperAPI](https://www.scraperapi.com/documentation)
- [Pricing](https://www.scraperapi.com/pricing)
