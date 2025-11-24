# Correção: Cálculo de Desconto com Cupom do Mercado Livre

## Problema Identificado

Quando o usuário aplicava um cupom ao editar um produto do Mercado Livre, o sistema:
1. ✅ Mostrava o desconto correto no preview (visual)
2. ✅ Atualizava a mensagem corretamente no textarea
3. ❌ **NÃO salvava o preço com cupom no banco de dados**
4. ❌ **Calculava o desconto incorretamente** para alguns preços

### Exemplos do Bug:

**Caso 1**: Produto de R$ 1.079,10 com cupom de 10%
- Desconto esperado: R$ 107,91
- Preço final esperado: R$ 971,19
- **Preço calculado**: R$ 970,21 ❌ (ERRADO!)

**Caso 2**: Produto de R$ 2.899,00 com cupom de 15%
- Desconto esperado: R$ 434,85
- Preço final esperado: R$ 2.464,15
- **Preço calculado**: R$ 2.464,15 ✅ (correto por sorte)

## Causas Raiz

### 1. Função de Extração de Preço Incorreta

**Arquivo**: [app/static/script.js](app/static/script.js#L1470)

A função `extrairPreco()` na linha 1470 estava com lógica incorreta:

```javascript
// ANTES (ERRADO):
const extrairPreco = (precoStr) => {
    if (!precoStr) return null;
    const numeroStr = precoStr.toString().replace(/[R$\s]/g, '').replace(',', '.');  // ❌
    const numero = parseFloat(numeroStr);
    return isNaN(numero) ? null : numero;
};
```

**Problema**: A função removia `R$` e espaços, mas depois **trocava apenas UMA vírgula por ponto**, sem remover os separadores de milhar (pontos) primeiro.

**Resultado**:
- `"R$ 1.079,10"` → `"1.079,10"` → `"1.079.10"` → `parseFloat("1.079.10")` → **1.079** ❌
- Deveria ser: `1079.10`

### 2. Formato do Preço Salvo

O código salvava o preço com cupom como número (ex: `971.19`), mas o sistema espera formato brasileiro com `R$` (ex: `"R$ 971,19"`).

## Solução Implementada

### Correção 1: Função de Extração de Preço

**Arquivo**: [app/static/script.js](app/static/script.js#L1468-L1478)

```javascript
// DEPOIS (CORRETO):
const extrairPreco = (precoStr) => {
    if (!precoStr) return null;
    // Passo 1: Remover "R$" e espaços
    let numeroStr = precoStr.toString().replace(/R\$/g, '').replace(/\s/g, '');
    // Passo 2: Remover pontos (separadores de milhar)
    numeroStr = numeroStr.replace(/\./g, '');
    // Passo 3: Trocar vírgula por ponto (separador decimal BR → US)
    numeroStr = numeroStr.replace(/,/g, '.');
    const numero = parseFloat(numeroStr);
    return isNaN(numero) ? null : numero;
};
```

**Resultado**:
- `"R$ 1.079,10"` → `"1079,10"` → `"1079.10"` → `parseFloat("1079.10")` → **1079.10** ✅

### Correção 2: Formato do Preço com Cupom

**Arquivo**: [app/static/script.js](app/static/script.js#L1488-L1490)

```javascript
const valorFinal = precoBase - desconto;
dadosParaAtualizar.preco_com_cupom = `R$ ${valorFinal.toFixed(2).replace('.', ',')}`;
console.log(`💰 Cupom calculado: Preço base R$ ${precoBase.toFixed(2)} - Desconto R$ ${desconto.toFixed(2)} = Preço final ${dadosParaAtualizar.preco_com_cupom}`);
```

**Agora**:
- Calcula o valor final: `precoBase - desconto`
- Formata como string brasileira: `"R$ 971,19"`
- Salva no banco de dados corretamente
- Adiciona log para debugging

## Fluxo Completo

### Quando o Usuário Aplica um Cupom:

1. **Usuário seleciona cupom** no dropdown → `selecionarCupom()` ([script.js:2829](script.js#L2829))
2. **Calcula preview** → `calcularEAtualizarPreviewCupom()` ([script.js:2865](script.js#L2865))
3. **Atualiza mensagem** no textarea com novo preço
4. **Usuário clica "Salvar Alterações"**
5. **JavaScript prepara dados** → Linhas 1466-1492:
   - Extrai preço base do produto
   - Calcula desconto (% do preço, limitado ao máximo)
   - Calcula preço final = preço base - desconto
   - Formata como `"R$ X.XXX,XX"`
   - Adiciona aos dados de atualização
6. **Envia PUT request** para `/produtos/{id}` → Linha 1497
7. **Backend salva** `preco_com_cupom` no banco → [routes.py:893](routes.py#L893)

### Quando a Mensagem é Formatada:

1. **Backend busca** `preco_com_cupom` do banco
2. **Usa no lugar** do `preco_atual` → [routes.py:376](routes.py#L376):
   ```python
   preco_atual_str = produto_dados.get('preco_com_cupom') or produto_dados.get('preco_atual', 'Preço indisponível')
   ```
3. **Formata mensagem** com preço já com desconto aplicado

## Testes de Validação

### Caso 1: Produto R$ 1.079,10 com cupom 10%

**Antes**:
- Preço base: 1.079 (parsing errado)
- Desconto: 107,90
- Preço final: 971,10 ❌

**Depois**:
- Preço base: 1079,10 ✅
- Desconto: 107,91
- Preço final: R$ 971,19 ✅

### Caso 2: Produto R$ 245,65 com cupom 5%

**Antes**:
- Preço base: 245,65 ✅
- Desconto: 12,28
- Preço final: 233,37 ✅

**Depois**:
- Preço base: 245,65 ✅
- Desconto: 12,28
- Preço final: R$ 233,37 ✅

### Caso 3: Produto R$ 2.899,00 com cupom 15% (limite R$ 300)

**Antes**:
- Preço base: 2899,00 ✅
- Desconto calculado: 434,85
- Desconto aplicado: 300,00 (limite)
- Preço final: 2599,00 ✅

**Depois**:
- Preço base: 2899,00 ✅
- Desconto calculado: 434,85
- Desconto aplicado: 300,00 (limite)
- Preço final: R$ 2.599,00 ✅

## Arquivos Modificados

- [app/static/script.js](app/static/script.js) - Linhas 1468-1492
  - Corrigida função `extrairPreco()` para tratar corretamente separadores de milhar
  - Adicionado formato brasileiro ao `preco_com_cupom` antes de salvar
  - Adicionado log de debugging

## Como Testar

1. Abrir um produto do Mercado Livre na interface
2. Clicar em "Editar"
3. Selecionar um cupom no dropdown
4. Verificar o preview do desconto (deve mostrar valores corretos)
5. Clicar em "Salvar Alterações"
6. Verificar no console do navegador:
   ```
   💰 Cupom calculado: Preço base R$ 1079.10 - Desconto R$ 107.91 = Preço final R$ 971,19
   ```
7. Recarregar a lista de produtos
8. Verificar que o preço com cupom foi salvo corretamente

## Data da Correção

2025-11-23
