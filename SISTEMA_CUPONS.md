# 🎟️ SISTEMA DE CUPONS - Promo Brothers

## 📋 COMO FUNCIONA

O sistema de cupons permite criar e gerenciar cupons de desconto que são aplicados automaticamente nas mensagens de produtos.

### Componentes:

1. **Tabela no Supabase** - Armazena os cupons
2. **Backend (Flask)** - API para gerenciar cupons
3. **Frontend** - Interface para criar/editar cupons
4. **Integração** - Cupons são usados nas mensagens

---

## 🚀 PASSO 1: Criar Tabela no Supabase

Execute o SQL no **Supabase SQL Editor**:

```bash
# Arquivo: SQL_TABELA_CUPONS.sql
```

Acesse: https://supabase.com/dashboard/project/SEU_PROJETO/sql

Cole o conteúdo do arquivo `SQL_TABELA_CUPONS.sql` e execute.

---

## 📱 PASSO 2: Acessar a Página de Cupons

1. Acesse: `http://SEU_IP/cupons-page`
2. Faça login se necessário
3. Clique em **➕ Novo Cupom**

---

## ➕ PASSO 3: Adicionar um Cupom

### Campos:

- **Código do Cupom**: Ex: `PROMO10` (será convertido para maiúsculas)
- **Porcentagem (%)**: Ex: `10` (desconto de 10%)
- **Limite de Desconto (R$)**: Ex: `30.00` (máximo R$ 30 de desconto)

### Exemplo 1:
```
Código: PROMO10
Porcentagem: 10%
Limite: R$ 30,00

Produto de R$ 200 → Desconto de R$ 20 (10% de 200)
Produto de R$ 500 → Desconto de R$ 30 (limite de R$ 30)
```

### Exemplo 2:
```
Código: MEGA20
Porcentagem: 20%
Limite: R$ 100,00

Produto de R$ 300 → Desconto de R$ 60 (20% de 300)
Produto de R$ 600 → Desconto de R$ 100 (limite de R$ 100)
```

---

## ✏️ PASSO 4: Usar Cupons nas Mensagens

### Antes (sem cupom):
```
🔥 Escrivaninha Ajl Store
✅ Por R$ 178,00
🛒 https://mercadolivre.com/sec/2v15ZXj
```

### Depois (com cupom):
```
🔥 Escrivaninha Ajl Store
Loja Validada no Mercado Livre

✅ Por R$ 160,20
🎟️ Use o cupom: PROMO10
🛒 https://mercadolivre.com/sec/2v15ZXj

☑️ Link do grupo: https://linktr.ee/promobrothers.shop
```

### Como funciona:
1. Preço original: R$ 178,00
2. Cupom PROMO10: 10% de desconto
3. Desconto: R$ 17,80
4. **Preço final: R$ 160,20**
5. Cupom inserido na mensagem automaticamente

---

## 🎯 FUNCIONALIDADES

### 1. Criar Cupom
- Clique em **➕ Novo Cupom**
- Preencha os campos
- Clique em **Salvar**

### 2. Editar Cupom
- Clique em **✏️ Editar** no cupom desejado
- Altere os campos
- Clique em **Salvar**

### 3. Ativar/Desativar Cupom
- Clique em **⏸️ Desativar** para desativar
- Clique em **▶️ Ativar** para ativar
- Cupons inativos não aparecem na lista de seleção

### 4. Excluir Cupom
- Clique em **🗑️ Excluir**
- Confirme a exclusão

---

## 📊 API ENDPOINTS

### Listar Cupons
```bash
GET /cupons
```

### Listar Cupons Ativos
```bash
GET /cupons/ativos
```

### Criar Cupom
```bash
POST /cupons
Content-Type: application/json

{
  "codigo": "PROMO10",
  "porcentagem": 10,
  "limite_valor": 30
}
```

### Atualizar Cupom
```bash
PUT /cupons/{id}
Content-Type: application/json

{
  "codigo": "PROMO15",
  "porcentagem": 15,
  "limite_valor": 50
}
```

### Deletar Cupom
```bash
DELETE /cupons/{id}
```

### Ativar/Desativar Cupom
```bash
PUT /cupons/{id}/toggle
Content-Type: application/json

{
  "ativo": false
}
```

### Calcular Valor com Cupom
```bash
POST /cupons/calcular
Content-Type: application/json

{
  "preco_original": 178.00,
  "cupom_id": 1
}

# Resposta:
{
  "success": true,
  "preco_original": 178.00,
  "desconto": 17.80,
  "valor_final": 160.20,
  "cupom_codigo": "PROMO10",
  "porcentagem": 10,
  "limite_valor": 30
}
```

---

## 🔧 INTEGRAÇÃO COM MENSAGENS

Os cupons serão aplicados automaticamente nas mensagens quando você:

1. **Agendar um produto**
2. **Enviar manualmente**
3. **Editar uma mensagem**

### Fluxo:

1. Usuário seleciona um produto
2. Sistema lista cupons ativos
3. Usuário escolhe um cupom
4. Sistema calcula o desconto
5. Mensagem é formatada com:
   - Preço com desconto
   - Código do cupom
   - Link de afiliado

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

- [ ] Executar `SQL_TABELA_CUPONS.sql` no Supabase
- [ ] Verificar se a tabela `cupons` foi criada
- [ ] Acessar `/cupons-page` no navegador
- [ ] Criar pelo menos 1 cupom de teste
- [ ] Verificar se o cupom aparece na lista
- [ ] Testar ativar/desativar cupom
- [ ] Integrar seleção de cupons na edição de mensagens

---

## 🐛 TROUBLESHOOTING

### Erro: "Cupom já existe com este código"
- Já existe um cupom com este código
- Use outro código ou edite o cupom existente

### Cupons não aparecem na lista
- Verifique se executou o SQL no Supabase
- Verifique as credenciais do Supabase no `.env`
- Verifique os logs do Flask

### Erro ao calcular desconto
- Verifique se o cupom está ativo
- Verifique se o `cupom_id` é válido
- Verifique se o preço original é maior que 0

---

## 📈 PRÓXIMOS PASSOS

1. ✅ Criar tabela no Supabase
2. ✅ Adicionar rotas no Flask
3. ✅ Criar interface de gerenciamento
4. 🔄 Integrar com edição de mensagens (próximo)
5. 🔄 Aplicar cupons automaticamente no agendamento

---

**Última atualização:** 2025-11-19
