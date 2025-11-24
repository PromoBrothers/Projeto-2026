# 📱 WhatsApp Monitor - Promo Brothers

Sistema completo de monitoramento de grupos do WhatsApp para capturar promoções de outros divulgadores e trocar automaticamente pelos seus códigos de afiliado.

## 🎯 Funcionalidades

- ✅ **Conexão via QR Code**: Interface amigável para conectar seu WhatsApp
- ✅ **Monitoramento de Grupos**: Escolha quais grupos monitorar
- ✅ **Detecção Automática de Links**: Identifica links de produtos em mensagens
- ✅ **Troca de Links de Afiliado**: Substitui automaticamente pelos seus links
- ✅ **Suporte Multi-Plataforma**:
  - Mercado Livre
  - Amazon
  - Shopee
  - Magazine Luiza
  - Americanas
  - AliExpress
- ✅ **Formatação Automática**: Usa o padrão de mensagem da aplicação
- ✅ **Interface Web Completa**: Gerencie tudo pela web

## 🚀 Como Usar

### 1. Instalar Dependências

Primeiro, navegue até a pasta do WhatsApp Monitor e instale as dependências:

```bash
cd whatsapp-monitor
npm install
```

### 2. Iniciar o Servidor WhatsApp

```bash
npm start
```

O servidor será iniciado na porta **3001**.

### 3. Iniciar o Flask (em outro terminal)

Na pasta raiz do projeto:

```bash
python run.py
```

O Flask será iniciado na porta **5000**.

### 4. Acessar a Interface

Abra seu navegador e acesse:

```
http://localhost:5000/whatsapp-monitor
```

### 5. Conectar seu WhatsApp

1. Na interface, aguarde o **QR Code** aparecer
2. Abra o WhatsApp no seu celular
3. Vá em **Configurações > Aparelhos conectados**
4. Clique em **Conectar um aparelho**
5. Escaneie o QR Code exibido na tela

### 6. Configurar Links de Afiliado

Antes de monitorar grupos, configure seus links de afiliado:

1. Na seção **"Links de Afiliado"**, selecione a plataforma
2. Cole seu link/código de afiliado
3. Clique em **"Salvar Configuração"**

Exemplo de configurações:

- **Mercado Livre**: Seu link de afiliado do ML
- **Amazon**: Sua tag de associado da Amazon
- **Shopee**: Seu link de afiliado da Shopee

### 7. Monitorar Grupos

1. Clique em **"Carregar Grupos"**
2. Escolha os grupos que deseja monitorar
3. Clique em **"Monitorar"** nos grupos selecionados

## 🔄 Como Funciona

### Fluxo de Processamento

```
1. Mensagem recebida no grupo monitorado
   ↓
2. Sistema extrai links de produtos
   ↓
3. Detecta a plataforma do link (ML, Amazon, etc)
   ↓
4. Chama a API Flask para processar o produto
   ↓
5. Flask faz scraping e pega detalhes do produto
   ↓
6. Substitui pelo seu link de afiliado
   ↓
7. Formata a mensagem no seu padrão
   ↓
8. Envia de volta no grupo com sua mensagem
```

### Exemplo Prático

**Mensagem Original:**
```
🔥 Oferta imperdível!
https://www.mercadolivre.com.br/produto/MLB123456
R$ 99,90
```

**Mensagem Processada (sua):**
```
⚡ *Nome do Produto*

🔥 *R$ 99,90*
🛒 https://mercadolivre.com.br/produto/MLB123456?seu_codigo_afiliado

👾 Grupo de ofertas: https://linktr.ee/promobrothers.shop
```

## ⚙️ Configurações Avançadas

### Variáveis de Ambiente

Você pode configurar as seguintes variáveis de ambiente:

**whatsapp-monitor/.env** (criar arquivo):
```env
PORT=3001
FLASK_API=http://localhost:5000
```

### Personalizar Padrão de Mensagem

O padrão de mensagem é definido na função `formatar_mensagem_marketing` em [app/routes.py:29-76](app/routes.py#L29-L76).

Para personalizar, edite essa função conforme suas necessidades.

## 📊 Interface Web

### Tela Principal

A interface possui 4 seções principais:

1. **Status da Conexão**
   - QR Code para autenticação
   - Estatísticas (grupos monitorados, links configurados)
   - Botão de logout

2. **Grupos Disponíveis**
   - Lista todos os grupos do WhatsApp
   - Indica quais estão sendo monitorados
   - Botões para iniciar/parar monitoramento

3. **Links de Afiliado**
   - Formulário para adicionar novos links
   - Lista de links configurados
   - Opção de remover links

4. **Log de Atividades**
   - Registro de todas as ações
   - Mensagens processadas
   - Erros e avisos

## 🔐 Segurança

- ✅ Sessão do WhatsApp é salva localmente em `auth_info_baileys/`
- ✅ Configurações salvas em `config.json`
- ✅ **NÃO compartilhe** esses arquivos (já estão no .gitignore)
- ✅ Use apenas em grupos que você tem permissão

## ⚠️ Observações Importantes

1. **WhatsApp Business**: Recomendado usar WhatsApp Business para evitar bloqueios
2. **Rate Limits**: O sistema respeita os limites do WhatsApp
3. **Mensagens Próprias**: O sistema ignora suas próprias mensagens
4. **Grupos Válidos**: Só monitora grupos do WhatsApp, não conversas individuais
5. **Processamento Assíncrono**: Mensagens são processadas em segundo plano

## 🐛 Resolução de Problemas

### WhatsApp não conecta

1. Certifique-se que o servidor Node está rodando (`npm start`)
2. Limpe a autenticação antiga:
   ```bash
   cd whatsapp-monitor
   rm -rf auth_info_baileys
   npm start
   ```
3. Gere um novo QR Code

### Mensagens não são processadas

1. Verifique se o grupo está marcado como "Monitorado"
2. Confirme que há links de afiliado configurados para a plataforma
3. Verifique o Log de Atividades na interface
4. Confirme que o Flask está rodando

### Erro ao processar produto

1. Verifique se a URL do produto é válida
2. Confirme que a plataforma é suportada
3. Verifique os logs do Flask no terminal

## 🔄 Comandos Úteis

```bash
# Instalar dependências
cd whatsapp-monitor && npm install

# Iniciar em modo desenvolvimento (reinicia automaticamente)
npm run dev

# Iniciar em modo produção
npm start

# Limpar autenticação
rm -rf auth_info_baileys

# Ver logs em tempo real
tail -f logs/whatsapp-monitor.log
```

## 📡 API Endpoints

O servidor WhatsApp Monitor expõe os seguintes endpoints:

- `GET /status` - Status da conexão
- `GET /qr` - QR Code para autenticação
- `GET /groups` - Lista grupos disponíveis
- `POST /groups/monitor` - Adiciona grupo ao monitoramento
- `DELETE /groups/monitor/:groupId` - Remove grupo do monitoramento
- `GET /affiliate/settings` - Lista configurações de afiliado
- `POST /affiliate/settings` - Salva configuração de afiliado
- `DELETE /affiliate/settings/:platform` - Remove configuração
- `POST /logout` - Desconecta do WhatsApp

## 📝 Logs

Os logs são exibidos em tempo real:

- **Console do Node.js**: Logs do WhatsApp e processamento
- **Interface Web**: Log de atividades
- **Console do Flask**: Logs de scraping e API

## 🚀 Inicialização Rápida

Execute ambos os servidores ao mesmo tempo:

**Windows:**
```batch
start cmd /k "cd whatsapp-monitor && npm start"
start cmd /k "python run.py"
```

**Linux/Mac:**
```bash
# Terminal 1
cd whatsapp-monitor && npm start

# Terminal 2 (nova aba)
python run.py
```

Depois acesse: http://localhost:5000/whatsapp-monitor

## 💡 Dicas

1. **Teste primeiro**: Use um grupo de teste antes de usar em produção
2. **Links corretos**: Sempre configure seus links de afiliado corretamente
3. **Monitore os logs**: Fique de olho no log de atividades
4. **Backup**: Faça backup do `config.json` periodicamente
5. **Atualizações**: Mantenha o Baileys atualizado (`npm update`)

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs no terminal
2. Consulte a seção "Resolução de Problemas"
3. Verifique se todas as dependências estão instaladas
4. Certifique-se que as portas 3001 e 5000 estão livres

## 🎉 Pronto!

Agora você tem um sistema completo de monitoramento de grupos do WhatsApp que automaticamente:

- Captura promoções de outros divulgadores
- Troca pelos seus links de afiliado
- Formata no seu padrão de mensagem
- Envia de volta no grupo

**Boa sorte com suas promoções!** 🚀
