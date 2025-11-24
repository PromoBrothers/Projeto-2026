# 🔧 Troubleshooting - WhatsApp Monitor

## Problema: Servidor mostra "Desconectado" e não gera QR Code

### Solução 1: Verificar se o servidor Node.js está rodando

1. Execute o script de teste:
   ```
   test-whatsapp.bat
   ```

2. Verifique no console se há erros
3. O servidor deve mostrar:
   ```
   🚀 Servidor WhatsApp Monitor rodando na porta 3001
   🔄 Iniciando conexão com WhatsApp...
   ✅ Estado de autenticação carregado
   ✅ Versão do Baileys: X.X.X
   ✅ Socket criado com sucesso
   📡 Connection update: { connection: 'connecting', hasQR: false }
   📱 QR Code gerado! Aguardando escaneamento...
   ```

### Solução 2: Limpar autenticação antiga

Se já conectou antes e está com problema:

```batch
cd whatsapp-monitor
rmdir /s /q auth_info_baileys
npm start
```

### Solução 3: Reinstalar dependências

```batch
cd whatsapp-monitor
rmdir /s /q node_modules
npm install
npm start
```

### Solução 4: Verificar porta 3001

A porta pode estar em uso:

```batch
netstat -ano | findstr :3001
```

Se estiver em uso, mate o processo:

```batch
taskkill /F /PID [NUMERO_DO_PID]
```

Depois reinicie:

```batch
cd whatsapp-monitor
npm start
```

### Solução 5: Usar o script de reinicialização

Execute:

```
restart-whatsapp.bat
```

Este script:
- Para o servidor antigo
- Inicia um novo
- Aguarda conexão

### Solução 6: Iniciar manualmente e verificar logs

1. Abra um terminal
2. Execute:
   ```batch
   cd whatsapp-monitor
   node server.js
   ```

3. Observe os logs no console
4. Procure por erros em vermelho
5. Copie a mensagem de erro completa

### Solução 7: Verificar versão do Node.js

O Baileys requer Node.js 16 ou superior:

```batch
node --version
```

Se a versão for inferior a 16, atualize:
👉 https://nodejs.org/

### Solução 8: Verificar conexão com a internet

O Baileys precisa conectar aos servidores do WhatsApp:

1. Verifique sua conexão
2. Desative VPN/Proxy temporariamente
3. Verifique firewall

### Solução 9: Aguardar mais tempo

Às vezes o QR Code demora para gerar:

1. Aguarde 10-15 segundos após iniciar
2. Recarregue a página (F5)
3. Observe o log de atividades na interface

## Logs Importantes

### Log Normal (Funcionando)

```
🚀 Servidor WhatsApp Monitor rodando na porta 3001
📡 Flask API: http://localhost:5000
📋 Configurações carregadas: { grupos: 0, afiliados: 0 }
🔄 Iniciando conexão com WhatsApp...
✅ Estado de autenticação carregado
✅ Versão do Baileys: 6.7.9
✅ Socket criado com sucesso
📡 Connection update: { connection: 'connecting', hasQR: false }
🔄 Conectando ao WhatsApp...
📡 Connection update: { connection: undefined, hasQR: true }
📱 QR Code gerado! Aguardando escaneamento...
✅ QR Code convertido para imagem e armazenado no cache
```

### Log com Erro

Se você ver algo como:

```
❌ Erro ao conectar ao WhatsApp: Error: ...
```

Copie o erro completo e:
1. Verifique a mensagem de erro
2. Pesquise no Google
3. Verifique se é problema de conexão/firewall

## Interface Web - Checklist

### Status Esperado (Aguardando QR)

- ⚠️ **Status**: Aguardando QR Code
- 📱 **QR Code**: Visível na tela
- 📊 **Grupos**: 0
- 🔗 **Links**: 0

### Status Esperado (Conectado)

- ✅ **Status**: Conectado
- 📱 **QR Code**: Não visível
- 📊 **Grupos**: (varia)
- 🔗 **Links**: (varia)
- 🔘 **Botão**: "Desconectar WhatsApp" visível

### Status com Problema

- ❌ **Status**: Desconectado
- 📱 **QR Code**: Não aparece
- ⚠️ **Log**: "Serviço não disponível" ou "Aguardando conexão..."

## Comandos de Diagnóstico

### Verificar se servidores estão rodando

```batch
REM WhatsApp Monitor (porta 3001)
netstat -ano | findstr :3001

REM Flask API (porta 5000)
netstat -ano | findstr :5000
```

### Ver processos Node.js

```batch
tasklist | findstr node.exe
```

### Matar todos os processos Node.js

```batch
taskkill /F /IM node.exe
```

## Passos Completos de Reset

Se nada funcionar, faça um reset completo:

1. **Parar tudo:**
   ```batch
   taskkill /F /IM node.exe
   taskkill /F /IM python.exe
   ```

2. **Limpar autenticação:**
   ```batch
   cd whatsapp-monitor
   rmdir /s /q auth_info_baileys
   del config.json
   ```

3. **Reinstalar dependências:**
   ```batch
   rmdir /s /q node_modules
   npm install
   ```

4. **Reiniciar tudo:**
   ```batch
   cd ..
   start-whatsapp-monitor.bat
   ```

5. **Aguardar 15 segundos**

6. **Recarregar página no navegador** (F5)

## Erros Comuns

### "Cannot find module '@whiskeysockets/baileys'"

**Solução:**
```batch
cd whatsapp-monitor
npm install
```

### "Port 3001 is already in use"

**Solução:**
```batch
netstat -ano | findstr :3001
taskkill /F /PID [PID_NUMBER]
```

### "QR Code não disponível"

**Solução:**
- Aguarde 10-15 segundos
- Recarregue a página
- Verifique logs no terminal do Node.js

### "WhatsApp Monitor não está rodando"

**Solução:**
1. Verifique se iniciou o servidor Node.js
2. Execute: `cd whatsapp-monitor && npm start`
3. Aguarde mensagem: "Servidor WhatsApp Monitor rodando"

## Verificação Final

Tudo funcionando quando você vê:

✅ Terminal do Node.js aberto com "Servidor WhatsApp Monitor rodando"
✅ Terminal do Flask aberto com "Running on http://0.0.0.0:5000"
✅ Interface web acessível em http://localhost:5000/whatsapp-monitor
✅ QR Code visível na interface (ou status "Conectado" se já autenticou)
✅ Log de atividades mostrando "Sistema iniciado"

## Ainda com Problemas?

1. Tire um print do erro no terminal
2. Tire um print da interface web
3. Copie os logs completos
4. Verifique se:
   - Node.js está instalado (v16+)
   - Portas 3001 e 5000 estão livres
   - Internet está funcionando
   - Não há firewall bloqueando

## Contato

Se persistir o problema, forneça:
- Versão do Node.js: `node --version`
- Versão do NPM: `npm --version`
- Sistema Operacional
- Logs completos do terminal
- Prints da interface
