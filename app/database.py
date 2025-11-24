# /mercado_livre_scraper/app/database.py

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def salvar_promocao(produto_dados, final_message=None, agendamento_data=None):
    """Salva os dados de uma promoção no Supabase."""
    try:
        if agendamento_data and isinstance(agendamento_data, datetime.datetime):
            agendamento_data = agendamento_data.isoformat()

        # Debug: verificar se tem imagem
        imagem = produto_dados.get("imagem")
        print(f"DEBUG: Salvando promoção - Tem imagem? {bool(imagem)}")
        if imagem:
            print(f"DEBUG: Tipo de imagem: {'base64' if imagem.startswith('data:') else 'URL'}")
            print(f"DEBUG: Tamanho da imagem: {len(imagem)} caracteres")

        data_to_insert = {
            "titulo": produto_dados.get("titulo"),
            "preco_atual": produto_dados.get("preco_atual"),
            "preco_original": produto_dados.get("preco_original"),
            "desconto": produto_dados.get("desconto"),
            "link_produto": produto_dados.get("link"),
            "link_afiliado": produto_dados.get("afiliado_link"),
            "imagem_url": imagem,
            "condicao": produto_dados.get("condicao"),
            "vendedor": produto_dados.get("vendedor"),
            "disponivel": produto_dados.get("disponivel"),
            "descricao": produto_dados.get("descricao"),
            "final_message": final_message,
            "agendamento": agendamento_data,
            "cupons": produto_dados.get("cupons", []),
            "processed_image_url": produto_dados.get("processed_image_url"),
            "fonte": produto_dados.get("fonte") # Adicionado para a visão unificada
        }

        supabase.table("promocoes").insert(data_to_insert).execute()
        print("DEBUG: Dados salvos no Supabase com sucesso!")
        return True

    except Exception as e:
        print(f"--- ERRO AO SALVAR NO SUPABASE ---: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def listar_produtos_db(status_filter, ordem_order, limit=200):
    """
    Lista produtos do Supabase com base nos filtros.

    OTIMIZAÇÕES:
    - Limit padrão de 200 produtos para performance
    - Ordenação otimizada por índice
    - Query mais eficiente
    """
    try:
        query = supabase.table("promocoes").select("*")

        if status_filter == 'agendado':
            query = query.not_.is_("agendamento", "null")
            query = query.order("agendamento", desc=(ordem_order == 'desc'))
        elif status_filter == 'nao-agendado':
            query = query.is_("agendamento", "null")
            # Ordenar por created_at descendente (mais recentes primeiro)
            query = query.order("created_at", desc=True)
        else:  # 'todos'
            query = query.order("created_at", desc=(ordem_order == 'desc'))

        # Limitar quantidade de resultados para performance
        query = query.limit(limit)

        response = query.execute()
        return response.data
    except Exception as e:
        print(f"Erro ao listar produtos: {e}")
        import traceback
        print(traceback.format_exc())
        return []

def deletar_produto_db(produto_id):
    """Deleta um produto do Supabase pelo ID."""
    return supabase.table("promocoes").delete().eq("id", produto_id).execute()

def agendar_produto_db(produto_id, agendamento_iso):
    """Atualiza o agendamento de um produto no Supabase."""
    return supabase.table("promocoes").update({'agendamento': agendamento_iso}).eq("id", produto_id).execute()

def obter_produto_db(produto_id):
    """Busca um produto específico no Supabase pelo ID."""
    try:
        response = supabase.table("promocoes").select("*").eq("id", produto_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Erro ao buscar produto no Supabase: {e}")
        return None

def atualizar_produto_db(produto_id, dados_atualizacao):
    """Atualiza dados específicos de um produto no Supabase."""
    return supabase.table("promocoes").update(dados_atualizacao).eq("id", produto_id).execute()

def upload_imagem_whatsapp(base64_string, titulo_produto, bucket_name='imagens_melhoradas_tech'):
    """
    Converte imagem base64 do WhatsApp e faz upload para Supabase Storage.
    Retorna a URL pública da imagem.
    """
    try:
        import base64
        import re
        from datetime import datetime

        # Extrair dados do base64
        if base64_string.startswith('data:image'):
            # Formato: data:image/jpeg;base64,/9j/4AAQSkZJRg...
            base64_data = base64_string.split(',')[1]
            # Detectar tipo de imagem
            if 'image/png' in base64_string:
                extensao = 'png'
            elif 'image/jpeg' in base64_string or 'image/jpg' in base64_string:
                extensao = 'jpg'
            elif 'image/webp' in base64_string:
                extensao = 'webp'
            else:
                extensao = 'jpg'  # Padrão
        else:
            base64_data = base64_string
            extensao = 'jpg'

        # Decodificar base64 para bytes
        image_bytes = base64.b64decode(base64_data)

        # Gerar nome simplificado do arquivo baseado no título
        # Remover caracteres especiais, deixar apenas letras, números e hífens
        nome_simplificado = re.sub(r'[^a-zA-Z0-9\s-]', '', titulo_produto)
        nome_simplificado = re.sub(r'\s+', '-', nome_simplificado.strip())
        nome_simplificado = nome_simplificado.lower()[:50]  # Limitar a 50 caracteres

        # Adicionar timestamp para evitar conflitos
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"whatsapp/{nome_simplificado}_{timestamp}.{extensao}"

        print(f"📤 Fazendo upload de imagem do WhatsApp: {file_name}")
        print(f"   Tamanho: {len(image_bytes)} bytes")

        # Upload da imagem
        upload_response = supabase.storage.from_(bucket_name).upload(
            file=image_bytes,
            path=file_name,
            file_options={"content-type": f"image/{extensao}"}
        )

        print(f"✅ Upload realizado: {file_name}")

        # Obter URL pública
        public_url_data = supabase.storage.from_(bucket_name).get_public_url(file_name)

        # Extrair URL (pode ser string ou dict)
        if isinstance(public_url_data, str):
            public_url = public_url_data
        elif isinstance(public_url_data, dict):
            public_url = public_url_data.get('publicUrl') or public_url_data.get('url') or str(public_url_data)
        else:
            public_url = str(public_url_data)

        print(f"✅ URL pública gerada: {public_url}")
        return public_url

    except Exception as e:
        print(f"❌ ERRO NO UPLOAD da imagem do WhatsApp: {e}")
        import traceback
        print(traceback.format_exc())
        return None

# As demais funções do database.py (listar_imagens_bucket, etc.) permanecem as mesmas.
def listar_imagens_bucket(bucket_name="imagens", pasta="", limit=50, offset=0, search_term=""):
    try:
        response = supabase.storage.from_(bucket_name).list(path=pasta, limit=limit, offset=offset)
        if not response:
            return []
        imagens = []
        for arquivo in response:
            nome = arquivo.get('name', '')
            if any(nome.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                if not search_term or search_term.lower() in nome.lower():
                    url_publica = supabase.storage.from_(bucket_name).get_public_url(f"{pasta}/{nome}" if pasta else nome)
                    imagens.append({
                        'nome': nome,
                        'url': url_publica,
                        'tamanho': arquivo.get('metadata', {}).get('size', 0),
                        'modificado_em': arquivo.get('updated_at', ''),
                        'path_completo': f"{pasta}/{nome}" if pasta else nome
                    })
        imagens.sort(key=lambda x: x.get('modificado_em', ''), reverse=True)
        return imagens
    except Exception as e:
        print(f"Erro ao listar imagens do bucket: {e}")
        return []

def obter_url_publica_imagem(bucket_name="imagens", caminho_arquivo=""):
    try:
        return supabase.storage.from_(bucket_name).get_public_url(caminho_arquivo)
    except Exception as e:
        print(f"Erro ao obter URL pública: {e}")
        return None

def listar_pastas_bucket(bucket_name="imagens", pasta_pai=""):
    try:
        response = supabase.storage.from_(bucket_name).list(path=pasta_pai)
        pastas = []
        for item in response:
            nome = item.get('name', '')
            if not any(nome.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.txt', '.json']):
                pastas.append({
                    'nome': nome,
                    'path_completo': f"{pasta_pai}/{nome}" if pasta_pai else nome
                })
        return pastas
    except Exception as e:
        print(f"Erro ao listar pastas do bucket: {e}")
        return []

# ============================================================================
# FUNÇÕES PARA GERENCIAR GRUPOS FIXOS DE AGENDAMENTO
# ============================================================================

def listar_grupos_fixos():
    """Lista todos os grupos fixos cadastrados para agendamentos automáticos."""
    try:
        response = supabase.table("grupos_fixos_agendamento").select("*").order("criado_em", desc=False).execute()
        return response.data
    except Exception as e:
        print(f"Erro ao listar grupos fixos: {e}")
        return []

def adicionar_grupo_fixo(grupo_id, grupo_nome):
    """Adiciona um novo grupo fixo para receber agendamentos automáticos."""
    try:
        # Verificar se o grupo já existe
        existing = supabase.table("grupos_fixos_agendamento").select("*").eq("grupo_id", grupo_id).execute()

        if existing.data and len(existing.data) > 0:
            # Grupo já existe, apenas atualizar o nome e ativar
            response = supabase.table("grupos_fixos_agendamento").update({
                "grupo_nome": grupo_nome,
                "ativo": True,
                "atualizado_em": datetime.datetime.now().isoformat()
            }).eq("grupo_id", grupo_id).execute()
            return {"success": True, "data": response.data, "message": "Grupo atualizado e ativado"}
        else:
            # Grupo não existe, inserir novo
            data = {
                "grupo_id": grupo_id,
                "grupo_nome": grupo_nome,
                "ativo": True
            }
            response = supabase.table("grupos_fixos_agendamento").insert(data).execute()
            return {"success": True, "data": response.data, "message": "Grupo adicionado"}
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Erro ao adicionar grupo fixo: {error_msg}")

        # Verificar se é erro de JSON
        if "Expecting value" in error_msg:
            return {"success": False, "error": "Erro de comunicação com o banco de dados. Verifique as credenciais do Supabase."}

        return {"success": False, "error": error_msg}

def remover_grupo_fixo(grupo_id):
    """Remove um grupo fixo da lista de agendamentos automáticos."""
    try:
        response = supabase.table("grupos_fixos_agendamento").delete().eq("grupo_id", grupo_id).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        print(f"Erro ao remover grupo fixo: {e}")
        return {"success": False, "error": str(e)}

def alternar_status_grupo_fixo(grupo_id, ativo):
    """Ativa ou desativa um grupo fixo."""
    try:
        response = supabase.table("grupos_fixos_agendamento").update({"ativo": ativo, "atualizado_em": datetime.datetime.now().isoformat()}).eq("grupo_id", grupo_id).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        print(f"Erro ao alternar status do grupo fixo: {e}")
        return {"success": False, "error": str(e)}

def listar_grupos_fixos_ativos():
    """Lista apenas os grupos fixos ativos."""
    try:
        response = supabase.table("grupos_fixos_agendamento").select("*").eq("ativo", True).execute()
        return response.data
    except Exception as e:
        print(f"Erro ao listar grupos fixos ativos: {e}")
        return []


# ============================================================================
# FUNÇÕES DE GERENCIAMENTO DE CUPONS
# ============================================================================

def listar_cupons():
    """Lista todos os cupons cadastrados."""
    try:
        response = supabase.table("cupons").select("*").order("criado_em", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Erro ao listar cupons: {e}")
        return []

def adicionar_cupom(codigo, porcentagem, limite_valor):
    """Adiciona um novo cupom."""
    try:
        # Verificar se o cupom já existe
        existing = supabase.table("cupons").select("*").eq("codigo", codigo).execute()

        if existing.data and len(existing.data) > 0:
            return {"success": False, "error": "Cupom já existe com este código"}

        data = {
            "codigo": codigo.upper(),
            "porcentagem": float(porcentagem),
            "limite_valor": float(limite_valor),
            "ativo": True
        }
        response = supabase.table("cupons").insert(data).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        print(f"Erro ao adicionar cupom: {e}")
        return {"success": False, "error": str(e)}

def atualizar_cupom(cupom_id, codigo, porcentagem, limite_valor):
    """Atualiza um cupom existente."""
    try:
        data = {
            "codigo": codigo.upper(),
            "porcentagem": float(porcentagem),
            "limite_valor": float(limite_valor),
            "atualizado_em": datetime.datetime.now().isoformat()
        }
        response = supabase.table("cupons").update(data).eq("id", cupom_id).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        print(f"Erro ao atualizar cupom: {e}")
        return {"success": False, "error": str(e)}

def remover_cupom(cupom_id):
    """Remove um cupom."""
    try:
        response = supabase.table("cupons").delete().eq("id", cupom_id).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        print(f"Erro ao remover cupom: {e}")
        return {"success": False, "error": str(e)}

def alternar_status_cupom(cupom_id, ativo):
    """Ativa ou desativa um cupom."""
    try:
        response = supabase.table("cupons").update({
            "ativo": ativo,
            "atualizado_em": datetime.datetime.now().isoformat()
        }).eq("id", cupom_id).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        print(f"Erro ao alternar status do cupom: {e}")
        return {"success": False, "error": str(e)}

def listar_cupons_ativos():
    """Lista apenas os cupons ativos."""
    try:
        response = supabase.table("cupons").select("*").eq("ativo", True).order("codigo").execute()
        return response.data
    except Exception as e:
        print(f"Erro ao listar cupons ativos: {e}")
        return []

def calcular_valor_com_cupom(preco_original, cupom_id):
    """Calcula o valor final com cupom aplicado."""
    try:
        # Buscar cupom
        cupom_response = supabase.table("cupons").select("*").eq("id", cupom_id).eq("ativo", True).execute()

        if not cupom_response.data or len(cupom_response.data) == 0:
            return {"success": False, "error": "Cupom não encontrado ou inativo"}

        cupom = cupom_response.data[0]
        porcentagem = cupom['porcentagem']
        limite_valor = cupom['limite_valor']

        # Calcular desconto
        desconto = preco_original * (porcentagem / 100)

        # Aplicar limite se necessário
        if desconto > limite_valor:
            desconto = limite_valor

        valor_final = preco_original - desconto

        return {
            "success": True,
            "preco_original": preco_original,
            "desconto": desconto,
            "valor_final": valor_final,
            "cupom_codigo": cupom['codigo'],
            "porcentagem": porcentagem,
            "limite_valor": limite_valor
        }
    except Exception as e:
        print(f"Erro ao calcular valor com cupom: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# FUNÇÕES PARA FILA DE MENSAGENS CLONADAS (ENVIO ESPAÇADO)
# ============================================================================

def adicionar_mensagem_fila(mensagem_dados: dict) -> dict:
    """
    Adiciona uma mensagem clonada à fila de envio.

    Args:
        mensagem_dados: {
            'mensagem_original': str,
            'mensagem_com_afiliado': str,
            'imagem_url': str (opcional),
            'grupo_origem': str,
            'grupo_origem_nome': str,
            'agendamento': datetime (opcional - se None, calcula automaticamente)
        }

    Returns:
        {'success': True/False, 'data': {...}, 'error': str}
    """
    try:
        # Calcular próximo horário de envio (intervalo de 5 min)
        agendamento = mensagem_dados.get('agendamento')

        if not agendamento:
            # Buscar última mensagem na fila para calcular próximo horário
            ultima_mensagem = supabase.table("fila_mensagens_clonadas")\
                .select("agendamento_envio")\
                .eq("status", "pendente")\
                .order("agendamento_envio", desc=True)\
                .limit(1)\
                .execute()

            if ultima_mensagem.data and len(ultima_mensagem.data) > 0:
                # Pegar último agendamento e adicionar 5 minutos
                ultimo_agendamento_str = ultima_mensagem.data[0]['agendamento_envio']
                ultimo_agendamento = datetime.datetime.fromisoformat(ultimo_agendamento_str.replace('Z', '+00:00'))
                proximo_envio = ultimo_agendamento + datetime.timedelta(minutes=5)
            else:
                # Primeira mensagem - enviar em 1 minuto
                proximo_envio = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=1)

            agendamento = proximo_envio.isoformat()
        elif isinstance(agendamento, datetime.datetime):
            agendamento = agendamento.isoformat()

        data_to_insert = {
            "mensagem_original": mensagem_dados.get('mensagem_original', ''),
            "mensagem_com_afiliado": mensagem_dados.get('mensagem_com_afiliado', ''),
            "imagem_url": mensagem_dados.get('imagem_url'),
            "grupo_origem": mensagem_dados.get('grupo_origem', ''),
            "grupo_origem_nome": mensagem_dados.get('grupo_origem_nome', ''),
            "agendamento_envio": agendamento,
            "status": "pendente",
            "tentativas": 0
        }

        response = supabase.table("fila_mensagens_clonadas").insert(data_to_insert).execute()

        print(f"✅ Mensagem adicionada à fila. Envio agendado para: {agendamento}")
        return {"success": True, "data": response.data, "agendamento": agendamento}

    except Exception as e:
        print(f"❌ Erro ao adicionar mensagem à fila: {e}")
        import traceback
        print(traceback.format_exc())
        return {"success": False, "error": str(e)}


def listar_fila_mensagens(status_filter: str = 'todos', limit: int = 100) -> list:
    """
    Lista mensagens na fila de envio.

    Args:
        status_filter: 'pendente', 'enviado', 'erro', 'todos'
        limit: número máximo de resultados

    Returns:
        Lista de mensagens
    """
    try:
        query = supabase.table("fila_mensagens_clonadas").select("*")

        if status_filter != 'todos':
            query = query.eq("status", status_filter)

        query = query.order("agendamento_envio", desc=False).limit(limit)

        response = query.execute()
        return response.data

    except Exception as e:
        print(f"❌ Erro ao listar fila de mensagens: {e}")
        return []


def obter_proxima_mensagem_fila() -> dict:
    """
    Obtém a próxima mensagem pendente que já passou do horário de envio.

    Returns:
        Mensagem ou None
    """
    try:
        agora = datetime.datetime.now(datetime.timezone.utc).isoformat()

        response = supabase.table("fila_mensagens_clonadas")\
            .select("*")\
            .eq("status", "pendente")\
            .lte("agendamento_envio", agora)\
            .order("agendamento_envio", desc=False)\
            .limit(1)\
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]

        return None

    except Exception as e:
        print(f"❌ Erro ao obter próxima mensagem: {e}")
        return None


def atualizar_status_mensagem_fila(mensagem_id: int, status: str, erro: str = None) -> dict:
    """
    Atualiza o status de uma mensagem na fila.

    Args:
        mensagem_id: ID da mensagem
        status: 'pendente', 'enviando', 'enviado', 'erro'
        erro: mensagem de erro (opcional)

    Returns:
        {'success': True/False}
    """
    try:
        update_data = {
            "status": status,
            "atualizado_em": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        if status == 'enviado':
            update_data["enviado_em"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if status == 'erro' and erro:
            update_data["erro_mensagem"] = erro
            # Incrementar tentativas
            mensagem = supabase.table("fila_mensagens_clonadas").select("tentativas").eq("id", mensagem_id).execute()
            if mensagem.data:
                update_data["tentativas"] = mensagem.data[0].get('tentativas', 0) + 1

        response = supabase.table("fila_mensagens_clonadas").update(update_data).eq("id", mensagem_id).execute()

        return {"success": True, "data": response.data}

    except Exception as e:
        print(f"❌ Erro ao atualizar status da mensagem: {e}")
        return {"success": False, "error": str(e)}


def deletar_mensagem_fila(mensagem_id: int) -> dict:
    """Remove uma mensagem da fila."""
    try:
        response = supabase.table("fila_mensagens_clonadas").delete().eq("id", mensagem_id).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        print(f"❌ Erro ao deletar mensagem da fila: {e}")
        return {"success": False, "error": str(e)}


def limpar_fila_enviadas(dias_antigos: int = 7) -> dict:
    """Remove mensagens enviadas há mais de X dias."""
    try:
        data_limite = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=dias_antigos)).isoformat()

        response = supabase.table("fila_mensagens_clonadas")\
            .delete()\
            .eq("status", "enviado")\
            .lt("enviado_em", data_limite)\
            .execute()

        return {"success": True, "deletados": len(response.data) if response.data else 0}

    except Exception as e:
        print(f"❌ Erro ao limpar fila: {e}")
        return {"success": False, "error": str(e)}


def obter_estatisticas_fila() -> dict:
    """Retorna estatísticas da fila de mensagens."""
    try:
        # Contar por status
        pendentes = supabase.table("fila_mensagens_clonadas").select("id", count="exact").eq("status", "pendente").execute()
        enviadas = supabase.table("fila_mensagens_clonadas").select("id", count="exact").eq("status", "enviado").execute()
        erros = supabase.table("fila_mensagens_clonadas").select("id", count="exact").eq("status", "erro").execute()

        # Próximo envio agendado
        proxima = supabase.table("fila_mensagens_clonadas")\
            .select("agendamento_envio")\
            .eq("status", "pendente")\
            .order("agendamento_envio", desc=False)\
            .limit(1)\
            .execute()

        proximo_envio = proxima.data[0]['agendamento_envio'] if proxima.data else None

        return {
            "pendentes": pendentes.count if hasattr(pendentes, 'count') else len(pendentes.data or []),
            "enviadas": enviadas.count if hasattr(enviadas, 'count') else len(enviadas.data or []),
            "erros": erros.count if hasattr(erros, 'count') else len(erros.data or []),
            "proximo_envio": proximo_envio
        }

    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {e}")
        return {"pendentes": 0, "enviadas": 0, "erros": 0, "proximo_envio": None}


