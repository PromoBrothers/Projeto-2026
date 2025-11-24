# Correção: Clonagem de Produtos do Mercado Livre com Link de Afiliado

## Problema Identificado

Quando o usuário clonava produtos do Mercado Livre, o sistema estava retornando **links de produtos diferentes** em vez do link de afiliado correto do produto original.

### Exemplo do Bug:
- **URL Original**: `https://www.mercadolivre.com.br/smartphone-samsung-galaxy-a05s-128gb-preto-4gb-ram/p/MLB36894633`
- **URL Retornada (ERRADA)**: `https://www.mercadolivre.com.br/garrafa-termica-1-litro-cafe-e-porta-frios-inox-com-tampa/p/MLB36894633?mshops=...`

Note que o código MLB é o mesmo (MLB36894633), mas a descrição do produto era diferente!

## Causa Raiz

A função `extrair_link_limpo_produto()` em [app/routes.py](app/routes.py#L163) estava tentando fazer **scraping da página do produto** para extrair o "link limpo" usando a meta tag `og:url`.

O problema era que:
1. O ScraperAPI retornava erro 403 Forbidden para Mercado Livre
2. O fallback (requisição direta) era bloqueado pelo anti-bot do ML
3. O HTML retornado era de uma página incorreta (redirect ou erro)
4. A meta tag `og:url` extraída era de um **produto diferente**

## Solução Implementada

Substituímos o scraping por **extração via regex**, que é:
- Mais rápido
- Mais confiável
- Não depende de requisições HTTP
- Garante que o código MLB permanece o mesmo

### Código Modificado

**Arquivo**: [app/routes.py](app/routes.py)
**Função**: `extrair_link_limpo_produto()` (linha 163)

```python
# ANTES (fazendo scraping - ERRADO):
elif 'mercadolivre.com' in url.lower():
    response = anti_bot.make_request_via_api(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    og_url = soup.find('meta', property='og:url')
    if og_url:
        link_limpo = og_url.get('content')  # ← Podia retornar produto errado!
        return link_limpo

# DEPOIS (usando regex - CORRETO):
elif 'mercadolivre.com' in url.lower():
    mlb_match = re.search(r'(MLB-?\d+)', url, re.IGNORECASE)
    if mlb_match:
        codigo = mlb_match.group(1).upper()
        codigo = codigo.replace('MLB-', 'MLB')  # Normalizar
        link_limpo = f"https://www.mercadolivre.com.br/p/{codigo}"
        return link_limpo
```

## Resultado

### Antes da Correção ❌
- Original: `https://www.mercadolivre.com.br/smartphone-samsung-galaxy-a05s-128gb-preto-4gb-ram/p/MLB36894633`
- Retornava: `https://www.mercadolivre.com.br/garrafa-termica-1-litro.../p/MLB36894633?mshops=...` (PRODUTO ERRADO!)

### Depois da Correção ✅
- Original: `https://www.mercadolivre.com.br/smartphone-samsung-galaxy-a05s-128gb-preto-4gb-ram/p/MLB36894633`
- Retorna: `https://www.mercadolivre.com.br/p/MLB36894633?mshops=gabrielvilelaluiz` (CORRETO!)

## Formatos de URL Suportados

A regex agora suporta todos os formatos de URL do Mercado Livre:

1. **Formato completo**:
   - `https://www.mercadolivre.com.br/smartphone-samsung-galaxy-a05s-128gb-preto-4gb-ram/p/MLB36894633`
   - → `https://www.mercadolivre.com.br/p/MLB36894633?mshops=gabrielvilelaluiz`

2. **Formato produto**:
   - `https://produto.mercadolivre.com.br/MLB-3456789012-notebook-lenovo-ideapad-1-15-intel-core-i3-4gb-256gb-ssd`
   - → `https://www.mercadolivre.com.br/p/MLB3456789012?mshops=gabrielvilelaluiz`

3. **Formato curto**:
   - `https://www.mercadolivre.com.br/p/MLB36894633`
   - → `https://www.mercadolivre.com.br/p/MLB36894633?mshops=gabrielvilelaluiz`

## Benefícios da Solução

1. **Velocidade**: Não precisa fazer requisição HTTP (instantâneo)
2. **Confiabilidade**: Não depende de anti-bot, ScraperAPI ou bloqueios
3. **Precisão**: Garante que o código MLB permanece exatamente o mesmo
4. **Simplicidade**: Código mais simples e fácil de manter

## Como Funciona o Fluxo Completo

1. **Usuário clona mensagem** com link do ML
2. `clone_message_with_affiliate()` chama `substituir_links_afiliado()`
3. `substituir_links_afiliado()` detecta link ML e chama `extrair_link_limpo_produto()`
4. `extrair_link_limpo_produto()` usa **regex** para extrair código MLB
5. Retorna URL limpa: `https://www.mercadolivre.com.br/p/MLB{codigo}`
6. `aplicar_afiliado_ml()` adiciona parâmetro `?mshops={affiliate_id}`
7. Link final: `https://www.mercadolivre.com.br/p/MLB{codigo}?mshops={affiliate_id}`

## Testes Realizados

Criei scripts de teste que validaram:
- ✅ Extração correta do código MLB de diferentes formatos de URL
- ✅ Normalização para formato canônico (`/p/MLB...`)
- ✅ Adição correta do parâmetro de afiliado (`?mshops=...`)
- ✅ Preservação do código MLB original (não retorna produtos diferentes)

## Arquivos Modificados

- [app/routes.py](app/routes.py) - Função `extrair_link_limpo_produto()` (linhas 189-214)

## Observação: ScraperAPI para ML

O ScraperAPI continua retornando **403 Forbidden** para Mercado Livre, o que indica que:
- Ou a chave API atingiu o limite de créditos
- Ou o ScraperAPI não consegue burlar o anti-bot do ML

Como a solução via regex funciona perfeitamente, **não é mais necessário usar ScraperAPI para Mercado Livre** neste contexto de extração de link limpo.

## Data da Correção

2025-11-23
