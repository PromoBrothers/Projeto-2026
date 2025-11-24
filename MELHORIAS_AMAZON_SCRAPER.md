# Melhorias no Scraper da Amazon

## Resumo das Alterações

O scraper da Amazon foi completamente refatorado para torná-lo mais robusto e confiável na extração de preços e dados de produtos.

## Principais Melhorias

### 1. **Extração de Preços Mais Robusta**

#### Estratégias Implementadas:

**Para Preço Atual:**
- ✅ Busca em múltiplos seletores CSS (.a-offscreen, .a-price, etc)
- ✅ Filtragem de preços de produtos relacionados/patrocinados
- ✅ Construção de preço a partir de partes (símbolo, inteiro, centavos)
- ✅ Validação de números para evitar preços inválidos
- ✅ Suporte a múltiplos formatos de preço da Amazon

**Para Preço Original (riscado):**
- ✅ Busca em containers de preços riscados (.basisPrice, s, .a-text-price)
- ✅ Validação para garantir que é diferente do preço atual
- ✅ Múltiplos fallbacks para diferentes layouts da Amazon

**Para Desconto:**
- ✅ Busca em badges e indicadores de desconto
- ✅ Cálculo automático baseado em preços (quando não explícito)
- ✅ Validação de percentuais (1-99%)

### 2. **Tratamento de Erros Robusto**

#### Sistema de Retry Automático:
- ✅ Retry automático em caso de erros 503, 500, 429
- ✅ Espera progressiva entre tentativas (backoff)
- ✅ Máximo de 3 tentativas para produtos individuais
- ✅ Máximo de 2 tentativas para páginas de busca
- ✅ Tratamento específico para erro 404 (produto não existe)

#### Validações:
- ✅ Verificação de conteúdo HTML válido
- ✅ Detecção de páginas vazias
- ✅ Logs detalhados para debugging
- ✅ Traceback completo em caso de erros

### 3. **Melhorias na Extração de Dados**

#### Nome do Produto:
- ✅ Múltiplos seletores de fallback
- ✅ Validação de tamanho mínimo

#### Imagem:
- ✅ Suporte a data-a-dynamic-image
- ✅ Fallback para src e data-old-hires
- ✅ Múltiplos seletores (#landingImage, #imgTagWrapperId, etc)

#### Ratings e Reviews:
- ✅ Mantidos os seletores existentes
- ✅ Tratamento de erros silencioso

### 4. **Logs Melhorados**

Agora os logs incluem:
- 🔍 Indicador visual de busca
- ✅ Confirmação de sucesso com detalhes
- ⚠️ Avisos de retry/problemas
- ❌ Erros claros
- 💰 Valores extraídos
- ⏳ Tempo de espera

## Arquivos Modificados

1. **[app/amazon_scraping.py](app/amazon_scraping.py)**
   - Função `extrair_preco_amazon()` - Linhas 176-339
   - Função `scrape_produto_amazon_especifico()` - Linhas 391-623
   - Função `scrape_amazon()` - Linhas 624-722

2. **[app/scraper_factory.py](app/scraper_factory.py)**
   - Classe `AmazonScraper._extract_product_data()` - Linhas 367-462

## Como Usar

### Scraping de Produto Específico

```python
from app import amazon_scraping

# Com retry automático (3 tentativas)
produto = amazon_scraping.scrape_produto_amazon_especifico(
    url="https://www.amazon.com.br/dp/ASIN123",
    afiliado_link="https://...",  # Opcional
    max_retries=3  # Padrão: 3
)

if produto:
    print(f"Preço: {produto['preco_atual']}")
    print(f"Original: {produto['preco_original']}")
    print(f"Desconto: {produto['desconto']}%")
else:
    print("Falha ao extrair produto")
```

### Busca de Produtos

```python
# Com retry automático (2 tentativas por página)
produtos = amazon_scraping.scrape_amazon(
    produto="Kindle",
    max_pages=2,
    max_retries=2  # Padrão: 2
)

print(f"Encontrados {len(produtos)} produtos")
for p in produtos:
    print(f"{p['nome']}: {p['preco_atual']}")
```

## Cenários Tratados

### ✅ Sucesso
- Extração completa de dados
- Logs de confirmação com valores

### ⚠️ Retry Automático
- Erro 503 (Service Unavailable)
- Erro 500 (Internal Server Error)
- Erro 429 (Too Many Requests)
- Página HTML vazia ou mal formatada

### ❌ Falha Definitiva
- Erro 404 → Retorna `None`
- Falha após todas as tentativas → Retorna `None` ou lista vazia
- Logs detalhados do erro

## Benefícios

1. **Maior Taxa de Sucesso**: Sistema de retry aumenta chances de extração
2. **Dados Mais Confiáveis**: Múltiplas estratégias garantem extração correta
3. **Melhor Debugging**: Logs detalhados facilitam identificação de problemas
4. **Resiliência**: Tolerância a falhas temporárias da Amazon
5. **Manutenibilidade**: Código organizado e comentado

## Testes Recomendados

Para testar as melhorias, experimente:

```python
# Teste 1: Produto individual
from app import amazon_scraping

produto = amazon_scraping.scrape_produto_amazon_especifico(
    "https://www.amazon.com.br/dp/[ASIN]"
)

# Teste 2: Busca
produtos = amazon_scraping.scrape_amazon("Notebook Dell", max_pages=1)
print(f"Total: {len(produtos)}")
produtos_com_preco = [p for p in produtos if p['preco_atual'] != 'Preço não disponível']
print(f"Com preço: {len(produtos_com_preco)}")
```

## Observações Importantes

- ⚠️ A Amazon pode bloquear requisições excessivas (erro 503)
- ⚠️ Use o proxy configurado no .env para melhores resultados
- ⚠️ Os tempos de espera ajudam a evitar bloqueios
- ⚠️ Alguns produtos podem não ter preço disponível (normal)

## Próximas Melhorias Sugeridas

- [ ] Implementar cache de resultados
- [ ] Adicionar suporte a variações de produtos
- [ ] Melhorar extração de especificações técnicas
- [ ] Implementar rotação de User-Agents
- [ ] Adicionar métricas de performance
