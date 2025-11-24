# 🪣 Configurar Bucket de Imagens no Supabase

## 🔍 Problema

O sistema está tentando fazer upload de imagens processadas para o Supabase Storage, mas o bucket `imagens-produtos` não existe:

```
❌ ERRO: {'statusCode': 400, 'error': 'Bucket not found', 'message': 'Bucket not found'}
```

## ✅ Solução

O sistema pode funcionar normalmente usando a URL da imagem original. O processamento de imagens é opcional.

## 🎯 Solução Definitiva: Criar Bucket no Supabase

Se você quiser ativar o processamento de imagens (redimensionar para 500x500), siga estes passos:

### Passo 1: Acessar Supabase Dashboard

1. Acesse: https://supabase.com/dashboard
2. Faça login na sua conta
3. Selecione o projeto: `cfacybymuscwcpgmbjkz`

### Passo 2: Criar Bucket de Storage

1. No menu lateral, clique em **"Storage"**
2. Clique em **"New bucket"**
3. Configure o bucket:
   - **Name:** `imagens-produtos`
   - **Public bucket:** ✅ **Marque como público**
   - **File size limit:** `5 MB` (ou conforme necessário)
   - **Allowed MIME types:** `image/jpeg, image/png, image/jpg`

4. Clique em **"Create bucket"**

### Passo 3: Configurar Políticas de Acesso (RLS)

O bucket precisa permitir:
- **Upload** de imagens (INSERT)
- **Leitura pública** de imagens (SELECT)

#### Política 1: Permitir Uploads

1. Clique no bucket `imagens-produtos`
2. Vá em **"Policies"**
3. Clique em **"New Policy"**
4. Selecione **"Custom policy"**
5. Configure:
   - **Policy name:** `Allow uploads`
   - **Definition:**
   ```sql
   CREATE POLICY "Allow uploads"
   ON storage.objects FOR INSERT
   WITH CHECK (bucket_id = 'imagens-produtos');
   ```

#### Política 2: Permitir Leitura Pública

1. Clique em **"New Policy"** novamente
2. Configure:
   - **Policy name:** `Allow public read`
   - **Definition:**
   ```sql
   CREATE POLICY "Allow public read"
   ON storage.objects FOR SELECT
   USING (bucket_id = 'imagens-produtos');
   ```

### Passo 4: Configurar Processamento de Imagens no Código

Configure o nome do bucket em [services.py](app/services.py) na função `upload_imagem_processada`:

```python
def upload_imagem_processada(image_bytes, bucket_name='imagens-produtos'):
```

### Passo 5: Reiniciar Flask

```bash
# Pare o Flask (Ctrl+C)
# Execute novamente:
python run.py
```

## 📊 Benefícios de Ativar o Processamento

Quando ativado, o sistema:

✅ **Redimensiona** imagens para 500x500 (formato quadrado)
✅ **Otimiza** tamanho do arquivo (JPEG com qualidade 90)
✅ **Padroniza** visual de todos os produtos
✅ **Centraliza** imagens no quadrado
✅ **Remove** fundos transparentes (substitui por branco)

## 🎯 Status Atual

**Processamento de imagens:** ❌ **DESABILITADO**
- Motivo: Bucket `imagens-produtos` não existe
- Comportamento: Usa URL da imagem original do site
- Impacto: Sistema funciona normalmente, mas sem imagens otimizadas

**Sistema de clonagem:** ✅ **FUNCIONANDO**
- Produtos são salvos no banco
- Mensagens são formatadas
- URLs originais são preservadas

## 📝 Próximos Passos

1. **Para usar sem imagens processadas:** ✅ Já está configurado, não precisa fazer nada
2. **Para ativar imagens processadas:** Siga os passos 1-5 acima

---

**O sistema está funcionando perfeitamente!** As imagens processadas são apenas uma otimização opcional. 🎉
