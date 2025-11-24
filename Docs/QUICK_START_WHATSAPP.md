# 🚀 Guia Rápido - WhatsApp Monitor

## ⚡ Início Rápido (3 Passos)

### 1️⃣ Instalar Node.js

Se ainda não tem o Node.js instalado:

👉 **Download**: https://nodejs.org/
- Baixe a versão LTS (recomendada)
- Instale com as opções padrão
- Reinicie o computador se necessário

### 2️⃣ Executar o Script de Inicialização

Basta dar duplo clique no arquivo:

```
start-whatsapp-monitor.bat
```

Este script irá:
- ✅ Verificar se o Node.js está instalado
- ✅ Instalar as dependências automaticamente
- ✅ Iniciar o servidor WhatsApp (porta 3001)
- ✅ Iniciar o servidor Flask (porta 5000)
- ✅ Abrir a interface no navegador

### 3️⃣ Conectar e Configurar

Quando a interface abrir no navegador:

1. **Escanear QR Code**
   - O QR Code aparecerá na tela
   - Abra o WhatsApp no celular
   - Vá em **Configurações > Aparelhos conectados**
   - Escaneie o código

2. **Configurar Links de Afiliado**
   - Selecione a plataforma (Mercado Livre, Amazon, etc)
   - Cole seu link de afiliado
   - Clique em "Salvar"

3. **Monitorar Grupos**
   - Clique em "Carregar Grupos"
   - Escolha os grupos para monitorar
   - Clique em "Monitorar"

## ✅ Pronto!

Agora o sistema irá:

- 👁️ Monitorar mensagens dos grupos selecionados
- 🔍 Detectar links de produtos automaticamente
- 🔄 Trocar pelos seus links de afiliado
- 📝 Formatar no seu padrão de mensagem
- 📤 Enviar de volta no grupo

## 🎯 Exemplo de Uso

**Mensagem detectada no grupo:**
```
Olha essa oferta!
https://www.mercadolivre.com.br/produto/MLB123456
```

**Sua mensagem automática:**
```
⚡ *Mouse Gamer RGB*

🔥 *R$ 89,90*
🛒 https://mercadolivre.com.br/...?SEU_CODIGO_AFILIADO

👾 Grupo de ofertas: https://linktr.ee/promobrothers.shop
```

## 📊 Acessar a Interface

Após iniciar, acesse:

🌐 **http://localhost:5000/whatsapp-monitor**

Ou clique no link "📱 WhatsApp Monitor" no menu da aplicação.

## ⚠️ Importante

- Use **WhatsApp Business** (recomendado)
- Configure seus links de afiliado ANTES de monitorar grupos
- Teste em um grupo privado primeiro
- Os servidores devem estar rodando simultaneamente

## 🔧 Comandos Manuais

Se preferir iniciar manualmente:

**Terminal 1 (WhatsApp):**
```bash
cd whatsapp-monitor
npm install
npm start
```

**Terminal 2 (Flask):**
```bash
python run.py
```

## 📱 Plataformas Suportadas

- ✅ Mercado Livre
- ✅ Amazon
- ✅ Shopee
- ✅ Magazine Luiza
- ✅ Americanas
- ✅ AliExpress

## 💡 Dicas

1. **Primeiro teste**: Use um grupo de teste com você mesmo
2. **Links válidos**: Certifique-se que seus links de afiliado estão corretos
3. **Monitore logs**: Acompanhe o "Log de Atividades" na interface
4. **Mantenha rodando**: Não feche as janelas dos servidores
5. **WhatsApp Business**: Evita bloqueios e tem mais recursos

## ❓ Problemas?

### QR Code não aparece
- Aguarde alguns segundos após iniciar
- Verifique se o servidor Node está rodando
- Recarregue a página (F5)

### Mensagens não são processadas
- Confirme que o grupo está "Monitorado"
- Verifique se há link de afiliado configurado para a plataforma
- Veja o Log de Atividades para detalhes

### Erro ao iniciar
- Verifique se as portas 3001 e 5000 estão livres
- Reinstale as dependências: `cd whatsapp-monitor && npm install`
- Certifique-se que o Python e Node.js estão instalados

## 📖 Documentação Completa

Para mais detalhes, consulte:
- [WHATSAPP_MONITOR_README.md](WHATSAPP_MONITOR_README.md)

## 🎉 Sucesso!

Agora você está pronto para capturar promoções e ganhar comissões automaticamente! 🚀💰
