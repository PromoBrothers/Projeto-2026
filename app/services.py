# /mercado_livre_scraper/app/services.py

import os
from dotenv import load_dotenv
import requests
import uuid
from PIL import Image
from io import BytesIO
from .database import supabase

load_dotenv()

USER_AGENT = os.getenv("USER_AGENT")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
N8N_AI_AGENT_URL = os.getenv("N8N_AI_AGENT_URL")

headers = {'User-Agent': USER_AGENT}

def processar_imagem_para_quadrado(url_imagem, tamanho_saida=(500, 500), cor_fundo=(255, 255, 255)):
    """
    Baixa e processa a imagem para o formato quadrado (500x500).
    """
    try:
        if not url_imagem:
            print("⚠️ URL da imagem não fornecida")
            return None

        print(f"🖼️ Processando imagem: {url_imagem[:80]}...")

        response = requests.get(url_imagem, headers=headers, timeout=15)
        response.raise_for_status()

        print(f"✅ Imagem baixada ({len(response.content)} bytes)")

        img_original = Image.open(BytesIO(response.content))
        print(f"✅ Imagem original: {img_original.size} - Modo: {img_original.mode}")

        if img_original.mode in ('RGBA', 'P', 'LA'):
            fundo = Image.new('RGB', img_original.size, cor_fundo)
            fundo.paste(img_original, (0, 0), img_original.convert('RGBA'))
            img = fundo
        else:
            img = img_original.convert('RGB')

        ratio = min(tamanho_saida[0] / img.size[0], tamanho_saida[1] / img.size[1])
        nova_largura = int(img.size[0] * ratio)
        nova_altura = int(img.size[1] * ratio)

        img_redimensionada = img.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)

        img_quadrada = Image.new('RGB', tamanho_saida, cor_fundo)
        pos_x = (tamanho_saida[0] - nova_largura) // 2
        pos_y = (tamanho_saida[1] - nova_altura) // 2
        img_quadrada.paste(img_redimensionada, (pos_x, pos_y))

        buffer = BytesIO()
        img_quadrada.save(buffer, format='JPEG', quality=90)
        buffer.seek(0)

        image_bytes = buffer.getvalue()
        print(f"✅ Imagem processada para {tamanho_saida} ({len(image_bytes)} bytes)")

        return image_bytes

    except Exception as e:
        print(f"❌ ERRO AO PROCESSAR IMAGEM: {e}")
        import traceback
        traceback.print_exc()
        return None

def processar_imagem_para_quadrado_from_bytes(image_bytes, tamanho_saida=(500, 500), cor_fundo=(255, 255, 255)):
    """
    Processa bytes de imagem para o formato quadrado (500x500).
    Útil quando já temos os bytes da imagem (ex: de base64)
    """
    try:
        if not image_bytes:
            print("⚠️ Bytes da imagem não fornecidos")
            return None

        print(f"🖼️ Processando imagem de bytes ({len(image_bytes)} bytes)...")

        img_original = Image.open(BytesIO(image_bytes))
        print(f"✅ Imagem original: {img_original.size} - Modo: {img_original.mode}")

        if img_original.mode in ('RGBA', 'P', 'LA'):
            fundo = Image.new('RGB', img_original.size, cor_fundo)
            fundo.paste(img_original, (0, 0), img_original.convert('RGBA'))
            img = fundo
        else:
            img = img_original.convert('RGB')

        ratio = min(tamanho_saida[0] / img.size[0], tamanho_saida[1] / img.size[1])
        nova_largura = int(img.size[0] * ratio)
        nova_altura = int(img.size[1] * ratio)

        img_redimensionada = img.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)

        img_quadrada = Image.new('RGB', tamanho_saida, cor_fundo)
        pos_x = (tamanho_saida[0] - nova_largura) // 2
        pos_y = (tamanho_saida[1] - nova_altura) // 2
        img_quadrada.paste(img_redimensionada, (pos_x, pos_y))

        buffer = BytesIO()
        img_quadrada.save(buffer, format='JPEG', quality=90)
        buffer.seek(0)

        processed_bytes = buffer.getvalue()
        print(f"✅ Imagem processada para {tamanho_saida} ({len(processed_bytes)} bytes)")

        return processed_bytes

    except Exception as e:
        print(f"❌ ERRO AO PROCESSAR IMAGEM FROM BYTES: {e}")
        import traceback
        traceback.print_exc()
        return None

def upload_imagem_processada(image_bytes, bucket_name='imagens-produtos'):
    """Faz o upload dos bytes de uma imagem para o Supabase Storage e retorna a URL pública."""
    try:
        file_name = f"processed_{uuid.uuid4()}.jpg"

        # Upload da imagem
        upload_response = supabase.storage.from_(bucket_name).upload(
            file=image_bytes,
            path=file_name,
            file_options={"content-type": "image/jpeg"}
        )

        print(f"✅ Upload realizado: {file_name}")

        # Obter URL pública
        public_url_data = supabase.storage.from_(bucket_name).get_public_url(file_name)

        # CORREÇÃO: Extrair apenas a string da URL
        # O Supabase pode retornar string diretamente OU um objeto com chave 'publicUrl'
        if isinstance(public_url_data, str):
            public_url = public_url_data
        elif isinstance(public_url_data, dict):
            public_url = public_url_data.get('publicUrl') or public_url_data.get('url') or str(public_url_data)
        else:
            # Fallback: converter para string
            public_url = str(public_url_data)

        print(f"✅ URL pública gerada: {public_url}")
        return public_url

    except Exception as e:
        print(f"❌ ERRO NO UPLOAD PARA O SUPABASE STORAGE: {e}")
        import traceback
        traceback.print_exc()
        return None

def enviar_para_webhook(payload):
    """Envia um payload para o webhook configurado."""
    return requests.post(
        WEBHOOK_URL,
        json=payload,
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mercado-Livre-Scraper/1.0'},
        timeout=60
    )

def formatar_mensagem_com_ia(produto_dados):
    """
    Envia os dados do produto para o agente de IA do n8n e retorna a mensagem formatada.
    """
    if not N8N_AI_AGENT_URL:
        raise Exception("N8N_AI_AGENT_URL não configurada no .env")
    
    try:
        payload = {
            "titulo": produto_dados.get('titulo', ''),
            "preco_atual": produto_dados.get('preco_atual', ''),
            "preco_original": produto_dados.get('preco_original'),
            "desconto": produto_dados.get('desconto'),
            "tem_promocao": produto_dados.get('tem_promocao', False),
            "link": produto_dados.get('afiliado_link') or produto_dados.get('link', ''),
            "fonte": produto_dados.get('fonte', ''),
            "plataforma": produto_dados.get('plataforma', ''),
            "loja": produto_dados.get('loja', '') # Adicionando a loja ao payload
        }
        
        response = requests.post(
            N8N_AI_AGENT_URL,
            json=payload,
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mercado-Livre-Scraper/1.0'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, dict) and 'message' in result:
                return result['message']
            elif isinstance(result, str):
                return result
            else:
                for key, value in result.items():
                    if isinstance(value, str) and len(value) > 10:
                        return value
                raise Exception(f"Formato de resposta inesperado: {result}")
        else:
            raise Exception(f"Agente de IA retornou status {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Erro ao formatar mensagem com IA: {e}")
        raise e