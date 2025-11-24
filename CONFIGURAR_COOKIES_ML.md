# 🔧 Como Configurar Cookies do Mercado Livre

Para gerar links de afiliado automaticamente, você precisa configurar os cookies de sessão do Mercado Livre no arquivo `.env`.

## 📋 Passo a Passo

### 1. Faça Login no Mercado Livre
Acesse https://www.mercadolivre.com.br e faça login com sua conta de afiliado.

### 2. Abra o DevTools
Pressione `F12` ou clique com botão direito → "Inspecionar"

### 3. Vá para a Aba Application
No DevTools, clique em **Application** (ou **Aplicação**)

### 4. Acesse os Cookies
No menu lateral esquerdo, expanda **Cookies** e clique em `https://www.mercadolivre.com.br`

### 5. Copie os Cookies
Você verá uma lista de cookies. Copie os valores dos seguintes cookies para o seu `.env`:

```env
# CSRF Token (obrigatório)
ML_CSRF_TOKEN=cole-aqui-o-valor-do-cookie-_csrf

# Cookies de Sessão
ML_COOKIE__CSRF=cole-aqui-o-valor-do-cookie-_csrf
ML_COOKIE_ORGNICKP=cole-aqui-o-valor-do-cookie-orgnickp
ML_COOKIE_ORGUSERIDP=cole-aqui-o-valor-do-cookie-orguseridp
ML_COOKIE_ORGUSERID=cole-aqui-o-valor-do-cookie-orguserid
ML_COOKIE__MLDATASESSIONID=cole-aqui-o-valor-do-cookie-_mldataSessionId
ML_COOKIE__D2ID=cole-aqui-o-valor-do-cookie-_d2id
ML_COOKIE_SSID=cole-aqui-o-valor-do-cookie-ssid
ML_COOKIE_FTID=cole-aqui-o-valor-do-cookie-ftid
ML_COOKIE_NSA_ROTOK=cole-aqui-o-valor-do-cookie-nsa_rotok
ML_COOKIE_X_MELI_SESSION_ID=cole-aqui-o-valor-do-cookie-x-meli-session-id
ML_COOKIE_CP=cole-aqui-o-valor-do-cookie-cp
```

### 6. Exemplo Real

```env
ML_CSRF_TOKEN=e9f8d7c6-b5a4-3210-9876-543210fedcba
ML_COOKIE__CSRF=e9f8d7c6-b5a4-3210-9876-543210fedcba
ML_COOKIE_ORGNICKP=PROMOBROTHERS
ML_COOKIE_ORGUSERIDP=123456789
ML_COOKIE_ORGUSERID=987654321
ML_COOKIE__MLDATASESSIONID=ABC123XYZ456
ML_COOKIE__D2ID=DEF789GHI012
ML_COOKIE_SSID=JKL345MNO678
ML_COOKIE_FTID=PQR901STU234
ML_COOKIE_NSA_ROTOK=VWX567YZA890
ML_COOKIE_X_MELI_SESSION_ID=BCD123EFG456
ML_COOKIE_CP=HIJ789KLM012
```

### 7. Reinicie a Aplicação
Após salvar o `.env`, reinicie o servidor Flask para aplicar as mudanças.

## ⚠️ Importante

- **Os cookies expiram!** Você precisará renovar periodicamente (geralmente a cada 30 dias)
- **Não compartilhe** seus cookies - eles dão acesso à sua conta
- Se os links pararem de funcionar, renove os cookies seguindo este guia novamente

## ✅ Como Testar

1. Aprove uma mensagem do WhatsApp com link do Mercado Livre
2. Verifique no log se aparece: `✅ Link de afiliado ML gerado via API`
3. O link deve estar no formato: `https://mercadolivre.com/sec/XXXXXX`

Se aparecer `⚠️ API não disponível`, significa que os cookies não estão configurados ou expiraram.
