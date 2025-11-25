# app/routes.py

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import datetime
import pytz
import time
import requests
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode # Importação adicionada para manipulação de URL
import os
import re
import logging


WHATSAPP_MONITOR_URL = os.getenv('WHATSAPP_MONITOR_URL', 'http://localhost:3001')# Criar logger
logger = logging.getLogger(__name__)

# Importa as funções dos outros módulos
from . import scraping, services, database
from . import amazon_scraping # Importa o módulo da Amazon

# Importa o novo sistema unificado
from .scraper_factory import ScraperFactory
from .queue_manager import queue_manager
from .monitoring import metrics_collector, health_checker, alert_manager
from .cache_manager import cache_manager
from .validators import product_validator

# Importa funções de afiliados do Mercado Livre
from .ml_affiliate import expandir_link_curto_ml

main_bp = Blueprint('main', __name__)

# Credenciais de login (em produção, use variáveis de ambiente)
LOGIN_USERNAME = os.getenv('LOGIN_USERNAME', 'promobrothers')
LOGIN_PASSWORD = os.getenv('LOGIN_PASSWORD', 'Bro46mo01')

# Decorator para proteger rotas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('main.login_page'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# ROTAS DE AUTENTICAÇÃO
# ============================================

@main_bp.route('/login', methods=['GET'])
def login_page():
    """Exibe a página de login"""
    # Se já estiver logado, redireciona para home
    if session.get('logged_in'):
        return redirect(url_for('main.index'))
    return render_template('login.html')

@main_bp.route('/login', methods=['POST'])
def login():
    """Processa o login"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        # Validar credenciais
        if username == LOGIN_USERNAME and password == LOGIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            session.permanent = True  # Manter sessão ativa

            logger.info(f'Login bem-sucedido: {username}')

            return jsonify({
                'success': True,
                'message': 'Login realizado com sucesso',
                'redirect': url_for('main.index')
            })
        else:
            logger.warning(f'Tentativa de login falhou: {username}')

            return jsonify({
                'success': False,
                'error': 'Usuário ou senha incorretos'
            }), 401

    except Exception as e:
        logger.error(f'Erro no login: {e}')
        return jsonify({
            'success': False,
            'error': 'Erro interno no servidor'
        }), 500

@main_bp.route('/logout')
def logout():
    """Faz logout do usuário"""
    session.clear()
    return redirect(url_for('main.login_page'))


# ⭐ NOVA FUNÇÃO: Aplica o ID de afiliado do Mercado Livre na URL
def aplicar_afiliado_ml(url: str) -> str:
    """
    Gera link de afiliado do Mercado Livre usando a API interna (cookies + cache inteligente).
    Se falhar, usa o método tradicional (parâmetro mshops).

    Performance:
    - Primeira vez: ~5-10s (descobre qual combinação funciona)
    - Próximas vezes: ~1s (usa cache) ⚡
    """
    logger.info(f'📥 aplicar_afiliado_ml chamado com URL: {url[:100] if url else "None"}...')

    # Importar o módulo de afiliado ML
    from .ml_affiliate import gerar_link_afiliado_ml

    ml_affiliate = os.getenv("MERCADOLIVRE_AFFILIATE_ID", "")

    # Se o ID não estiver configurado, retorna a URL original
    if not ml_affiliate or ml_affiliate == "seu-id-mercadolivre":
        logger.warning('⚠️ MERCADOLIVRE_AFFILIATE_ID não configurado.')
        return url

    # Aplica somente a links do Mercado Livre
    logger.info(f'🔍 Verificando se é link ML... mercadolivre.com: {"mercadolivre.com" in url.lower()}, mlb-: {"mlb-" in url.lower()}')

    if 'mercadolivre.com' in url.lower() or 'mlb-' in url.lower():
        try:
            # MÉTODO 1: Tentar gerar link via API (usando cookies e CSRF token + cache inteligente)
            try:
                affiliate_link = gerar_link_afiliado_ml(url)

                if affiliate_link:
                    logger.info(f'✅ Link de afiliado ML gerado via API: {affiliate_link[:80]}...')
                    return affiliate_link
                else:
                    logger.info('ℹ️ API não disponível, usando método tradicional (mshops)...')
            except Exception as e:
                logger.warning(f'⚠️ Erro ao gerar link via API: {e}. Usando método tradicional...')

            # MÉTODO 2 (FALLBACK): Injetar parâmetro mshops na URL
            parsed_url = urlparse(url)
            query = parse_qs(parsed_url.query)

            # Se já houver um parâmetro 'mshops', assume que já é o link de afiliado e retorna
            if 'mshops' in query or 'mshopps' in query:
                return url

            # Injetar o ID de afiliado
            query['mshops'] = [ml_affiliate]

            # Reconstruir o URL com o novo parâmetro
            parsed_url = parsed_url._replace(query=urlencode(query, doseq=True))
            fallback_url = urlunparse(parsed_url)

            logger.info(f'✅ Link de afiliado ML gerado via método tradicional (mshops)')
            return fallback_url

        except Exception as e:
            logger.error(f'❌ Erro ao injetar afiliado na URL {url}: {e}')
            return url
    return url


def extrair_link_limpo_produto(url):
    """
    Acessa a página do produto via ScraperAPI e extrai o link do botão Compartilhar.
    Retorna o link limpo do produto sem parâmetros extras.
    """
    try:
        from bs4 import BeautifulSoup
        from .anti_bot import AntiBotManager

        logger.info(f'🔍 Fazendo scraping para extrair link limpo de: {url[:80]}...')

        # Amazon - usar regex (mais rápido e confiável)
        if 'amazon.com' in url.lower():
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
            if not asin_match:
                asin_match = re.search(r'/gp/product/([A-Z0-9]{10})', url)

            if asin_match:
                asin = asin_match.group(1)
                link_limpo = f"https://www.amazon.com.br/dp/{asin}"
                logger.info(f'✅ Link limpo Amazon extraído (regex): {link_limpo}')
                return link_limpo
            else:
                logger.warning('⚠️ Não conseguiu extrair ASIN da URL Amazon')
                return url

        # Mercado Livre - usar regex (mais rápido e confiável, evita scraping que pode retornar produto errado)
        elif 'mercadolivre.com' in url.lower() or 'mercadolibre.com' in url.lower():
            try:
                # Tentar extrair o código MLB da URL usando regex
                # Suporta formatos:
                # - https://www.mercadolivre.com.br/produto/p/MLB1234567890
                # - https://produto.mercadolivre.com.br/MLB-1234567890-descricao
                # - https://www.mercadolivre.com.br/p/MLB1234567890

                mlb_match = re.search(r'(MLB-?\d+)', url, re.IGNORECASE)
                if mlb_match:
                    codigo = mlb_match.group(1).upper()
                    # Normalizar formato (remover hífen se tiver)
                    codigo = codigo.replace('MLB-', 'MLB')

                    # Retornar URL limpa no formato canônico /p/MLB...
                    link_limpo = f"https://www.mercadolivre.com.br/p/{codigo}"
                    logger.info(f'✅ Link limpo Mercado Livre extraído (regex): {link_limpo}')
                    return link_limpo
                else:
                    logger.warning('⚠️ Não conseguiu extrair código MLB da URL')
                    return url

            except Exception as ml_error:
                logger.error(f'❌ Erro ao extrair código MLB: {str(ml_error)}')
                return url

        # Outras plataformas - retornar URL original
        return url

    except Exception as e:
        logger.error(f'❌ Erro geral ao extrair link limpo: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return url


def substituir_links_afiliado(mensagem):
    """
    Detecta links de produtos na mensagem e substitui por links de afiliado configurados.
    Suporta: Amazon, Mercado Livre, Shopee, Magazine Luiza, Americanas

    TAMBÉM substitui links de grupos/WhatsApp/Telegram pelo link oficial do Promo Brothers.

    NOVO: Detecta links curtos de afiliado ML (/sec/...) e os expande para obter o produto real,
    gerando comissão para o criador original e depois criando seu próprio link de afiliado.
    """
    # Tags de afiliado do .env
    amazon_tag = os.getenv("AMAZON_ASSOCIATES_TAG", "promobrothers-20")
    ml_affiliate = os.getenv("MERCADOLIVRE_AFFILIATE_ID", "")

    # Link oficial do grupo Promo Brothers
    LINK_GRUPO_OFICIAL = "https://linktr.ee/promobrothers.shop"

    # Regex para detectar URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, mensagem)

    mensagem_modificada = mensagem
    links_substituidos = []

    for url in urls:
        url_original = url
        plataforma = None
        url_modificada = url

        # PASSO 0: Detectar e substituir links de grupos/convite
        url_lower = url.lower()
        is_grupo_link = any(padrao in url_lower for padrao in [
            'chat.whatsapp.com',      # Links de grupo WhatsApp
            'wa.me/group',            # Links de grupo WhatsApp
            't.me/',                  # Links de Telegram
            'linktr.ee',              # Linktree (se não for o nosso)
            'bit.ly',                 # Encurtadores comuns usados para grupos
            'cutt.ly',
            'grupo',                  # URLs com "grupo" no nome
        ])

        # Se for link de grupo E não for o nosso link oficial
        if is_grupo_link and 'promobrothers' not in url_lower:
            plataforma = 'Link do Grupo'
            url_modificada = LINK_GRUPO_OFICIAL

        # PASSO 0.5: Detectar links curtos de afiliado ML (/sec/...) e expandir
        elif 'mercadolivre.com/sec/' in url_lower or 'mercadolibre.com/sec/' in url_lower:
            logger.info(f'🔗 Detectado link curto de afiliado ML: {url}')

            # Expandir o link curto para obter a URL real do produto
            url_produto_real = expandir_link_curto_ml(url)

            if url_produto_real:
                logger.info(f'✅ Link expandido: {url_produto_real}')
                # Usar a URL real do produto como base para gerar nosso afiliado
                url_limpo = extrair_link_limpo_produto(url_produto_real)
                plataforma = 'Mercado Livre (clonado)'

                # Aplicar nosso afiliado
                if ml_affiliate and ml_affiliate != "seu-id-mercadolivre":
                    url_modificada = aplicar_afiliado_ml(url_limpo)
                else:
                    url_modificada = url_limpo
            else:
                logger.warning('⚠️ Não foi possível expandir o link curto. Mantendo original.')
                url_modificada = url

        # PASSO 1: Extrair link limpo do produto (remove parâmetros de afiliado de terceiros)
        elif 'amazon.com' in url_lower or 'amzn.to' in url_lower or 'mercadolivre.com' in url_lower or 'shopee.com' in url_lower:
            url_limpo = extrair_link_limpo_produto(url)

            # PASSO 2: Adicionar SEU link de afiliado
            url_modificada = url_limpo

            # Amazon
            if 'amazon.com' in url_limpo.lower() or 'amzn.to' in url_limpo.lower():
                plataforma = 'Amazon'
                if 'amzn.to' not in url_limpo:  # Links encurtados não modificamos
                    # Adicionar tag de afiliado ao link limpo
                    separator = '&' if '?' in url_limpo else '?'
                    url_modificada = f"{url_limpo}{separator}tag={amazon_tag}&linkCode=osi"

            # Mercado Livre
            elif 'mercadolivre.com' in url_limpo.lower() or 'mlb-' in url_limpo.lower():
                plataforma = 'Mercado Livre'
                if ml_affiliate and ml_affiliate != "seu-id-mercadolivre":
                    # Adicionar ID de afiliado do Mercado Livre - USANDO A NOVA FUNÇÃO SIMPLIFICADA
                    url_modificada = aplicar_afiliado_ml(url_limpo)

            # Shopee
            elif 'shopee.com' in url.lower():
                plataforma = 'Shopee'
                shopee_id = os.getenv("SHOPEE_AFFILIATE_ID", "")
                if shopee_id and shopee_id != "seu-id-shopee":
                    separator = '&' if '?' in url else '?'
                    url_modificada = f"{url}{separator}affiliate={shopee_id}"

        # Se houve modificação, substituir na mensagem
        if url_modificada != url_original:
            mensagem_modificada = mensagem_modificada.replace(url_original, url_modificada)
            links_substituidos.append({
                'plataforma': plataforma,
                'original': url_original,
                'modificada': url_modificada
            })

    # PASSO FINAL: Garantir que existe o link do grupo no final
    # Se a mensagem tiver "Link do grupo" mas não tiver nosso link, adicionar
    if 'link do grupo' in mensagem_modificada.lower() and LINK_GRUPO_OFICIAL not in mensagem_modificada:
        # Tentar encontrar e substituir padrões comuns
        padroes_grupo = [
            r'(?:☑️|✅|👥|📱)?\s*[Ll]ink\s+d[oe]\s+[Gg]rupo[:\s]*[^\n]*',
        ]
        for padrao in padroes_grupo:
            match = re.search(padrao, mensagem_modificada)
            if match:
                mensagem_modificada = re.sub(padrao, f'☑️ Link do grupo: {LINK_GRUPO_OFICIAL}', mensagem_modificada)
                links_substituidos.append({
                    'plataforma': 'Link do Grupo (texto)',
                    'original': match.group(0),
                    'modificada': f'☑️ Link do grupo: {LINK_GRUPO_OFICIAL}'
                })
                break

    return mensagem_modificada, links_substituidos


def extrair_valor_numerico(preco_str):
    """Função auxiliar para converter string de preço em float."""
    if not preco_str:
        return 0.0
    try:
        # Lógica robusta para tratar formatos como "1.079,10" e "1,079,10"
        preco_limpo = str(preco_str).replace('R$', '').strip().replace('.', '').replace(',', '.')
        return float(preco_limpo)
    except (ValueError, TypeError):
        return 0.0

def formatar_mensagem_marketing(produto_dados):
    """
    Formata a mensagem de marketing com o NOVO PADRÃO do usuário:
    
    🔥 *{Titulo}*
    * _{Vendedor ou Condição}_

    ✅ De ~{Preco Original}~ → Por *{Preco Atual}*
    🎟️ *Cupom: {Cupom Texto}*
    🛒 {Link Afiliado ou Produto}
    
    👥 Link do grupo: https://linktr.ee/promobrothers.shop
    """
    titulo = produto_dados.get('titulo', 'Produto em Destaque')
    
    # GARANTIA DO LINK DE AFILIADO/RASTREIO: 
    # 1. Tenta o link de afiliado preenchido no formulário de cupom
    # 2. Tenta o link de afiliado explícito do produto
    # 3. Usa o link base do produto e aplica o ID de afiliado ML
    
    cupom_info = produto_dados.get('cupom_aplicado')
    link_base = produto_dados.get('link', 'Link não disponível')
    link_afiliado_expl = produto_dados.get('afiliado_link')

    link = (
        (cupom_info.get('link_afiliado') if cupom_info and cupom_info.get('link_afiliado') else None)
        or link_afiliado_expl
        or link_base
    )

    # ⭐ IMPORTANTE: Aplica a função de afiliado do ML no link final antes de usar na mensagem
    logger.info(f'🔗 Link ANTES de aplicar afiliado: {link[:100] if link else "None"}...')
    link = aplicar_afiliado_ml(link)
    logger.info(f'🔗 Link DEPOIS de aplicar afiliado: {link[:100] if link else "None"}...')
    
    # Preço atual é o preço com cupom se existir, senão o preço atual do scraping
    preco_atual_str = produto_dados.get('preco_com_cupom') or produto_dados.get('preco_atual', 'Preço indisponível')
    preco_original_str = produto_dados.get('preco_original')
    
    # Tenta obter info do vendedor/condição
    vendedor_info_raw = produto_dados.get('vendedor') or produto_dados.get('condicao') or 'Informação não disponível'

    # Formatar vendedor_info: adicionar espaços entre palavras grudadas
    vendedor_info = vendedor_info_raw
    # Adicionar espaço antes de letras maiúsculas que vêm depois de minúsculas
    # Exemplo: "oficialPlayStation" → "oficial PlayStation"
    vendedor_info = re.sub(r'([a-z])([A-Z])', r'\1 \2', vendedor_info)
    # Adicionar espaço entre "Loja" e palavra seguinte
    # Exemplo: "LojaOficial" → "Loja Oficial"
    vendedor_info = re.sub(r'(Loja)([A-Z])', r'\1 \2', vendedor_info)
    # Adicionar espaço entre "oficial" e palavra seguinte
    # Exemplo: "oficialPlayStation" → "oficial PlayStation"
    vendedor_info = re.sub(r'(oficial)([A-Z])', r'\1 \2', vendedor_info)
    # Adicionar espaço antes de "Vendido"
    # Exemplo: "PlayStationVendido" → "PlayStation Vendido"
    vendedor_info = re.sub(r'([a-zA-Z])Vendido', r'\1 Vendido', vendedor_info)
    # Adicionar espaço depois de "por"
    # Exemplo: "porWEBFONES" → "por WEBFONES"
    vendedor_info = re.sub(r'por([A-Z])', r'por \1', vendedor_info)
    
    # Informações de Cupom
    
    # Tenta definir o cupom
    cupom_texto = 'SEM CUPOM' 
    if cupom_info and cupom_info.get('texto'):
        cupom_texto = cupom_info['texto']
    elif produto_dados.get('cupons') and isinstance(produto_dados['cupons'], list) and produto_dados['cupons']:
        cupom_texto = produto_dados['cupons'][0]
    
    
    # MONTAGEM DA MENSAGEM
    mensagem = f"🔥 *{titulo}*\n"
    mensagem += f"* _{vendedor_info}_\n\n"
    
    # Bloco de Preços
    if preco_original_str and preco_original_str != preco_atual_str:
        mensagem += f"✅ De ~{preco_original_str}~ → Por *{preco_atual_str}*\n"
    else:
        # Se não houver preço original/promoção, exibe só o preço atual
        mensagem += f"✅ Preço: {preco_atual_str}\n"
        
    # Bloco de Cupom e Link
    mensagem += f"🎟️ Use o cupom: *{cupom_texto}*\n"
    mensagem += f"🛒 {link}\n\n"
    
    # Bloco final
    mensagem += "👥 Link do grupo: https://linktr.ee/promobrothers.shop"
        
    return mensagem.strip()

@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')

@main_bp.route('/cupons-page')
@login_required
def cupons_page():
    """Página de gerenciamento de cupons"""
    return render_template('cupons.html')

@main_bp.route('/amazon')
@login_required
def amazon():
    return render_template('amazon.html')

@main_bp.route('/afiliados')
def afiliados():
    return render_template('afiliados.html')


@main_bp.route('/teste')
def teste():
    return jsonify({'status': 'funcionando', 'mensagem': 'Flask está rodando!'})

@main_bp.route('/buscar', methods=['POST'])
def buscar():
    try:
        data = request.get_json()
        produto = data.get('produto', '').strip()
        if not produto:
            return jsonify({'error': 'Produto não pode estar vazio'}), 400
        max_pages = data.get('max_pages', 2)
        resultados = scraping.scrape_mercadolivre(produto, max_pages)
        if not resultados:
            resultados = scraping.busca_alternativa(produto)
        return jsonify({'success': True, 'resultados': resultados, 'total': len(resultados)})
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/buscar-amazon', methods=['POST'])
def buscar_amazon():
    try:
        data = request.get_json()
        produto = data.get('produto', '').strip()
        if not produto:
            return jsonify({'error': 'Produto não pode estar vazio'}), 400
        max_pages = data.get('max_pages', 2)
        categoria = data.get('categoria', '')
        resultados = amazon_scraping.scrape_amazon(produto, max_pages, categoria)
        return jsonify({'success': True, 'produtos': resultados, 'total': len(resultados)})
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/produto-amazon', methods=['POST'])
def produto_amazon():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        afiliado_link = data.get('afiliado_link', '').strip()
        if not url:
            return jsonify({'error': 'URL não pode estar vazia'}), 400
        if not ('amazon.com' in url or 'amzn.to' in url):
            return jsonify({'error': 'URL deve ser da Amazon'}), 400
        produto = amazon_scraping.scrape_produto_amazon_especifico(url, afiliado_link)
        return jsonify({'success': True, 'produto': produto})
    except Exception as e:
        return jsonify({'error': f'Erro ao analisar produto: {str(e)}'}), 500

@main_bp.route('/buscar-afiliados', methods=['POST'])
def buscar_afiliados():
    try:
        data = request.get_json()
        produto = data.get('produto', '').strip()
        if not produto:
            return jsonify({'error': 'Produto não pode estar vazio'}), 400
        max_pages = data.get('max_pages', 2)
        plataforma = data.get('plataforma', 'todas')
        ordenacao = data.get('ordenacao', 'relevancia')
        preco_min = data.get('preco_min', '')
        preco_max = data.get('preco_max', '')
        from . import affiliate_scraping
        resultados = affiliate_scraping.scrape_afiliados(
            produto=produto, max_pages=max_pages, plataforma=plataforma,
            ordenacao=ordenacao, preco_min=preco_min, preco_max=preco_max
        )
        return jsonify({'success': True, 'produtos': resultados, 'total': len(resultados)})
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/produto', methods=['POST'])
def buscar_produto():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'error': 'URL não pode estar vazia'}), 400
        if 'mercadolivre.com' not in url and 'mercadolibre.com' not in url:
            return jsonify({'error': 'URL deve ser do Mercado Livre'}), 400
        produto = scraping.scrape_produto_especifico(url)
        if produto:
            return jsonify({'success': True, 'produto': produto})
        else:
            return jsonify({'error': 'Não foi possível extrair informações do produto'}), 404
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/processar_para_envio', methods=['POST']) # Rota renomeada de /webhook para /processar_para_envio
def processar_para_envio():
    produto_para_salvar = {}
    try:
        data = request.get_json()
        tipo = data.get('type', 'mensagem')
        afiliado_link = data.get('afiliado_link', '').strip()
        
        if tipo == 'produto':
            produto_dados = data.get('produto', {})
            if not produto_dados:
                return jsonify({'error': 'Dados do produto não podem estar vazios'}), 400
            
            produto_para_salvar = produto_dados.copy()
            produto_para_salvar['afiliado_link'] = afiliado_link or produto_dados.get('link')
            
            # ⭐ Aplica o ID de afiliado na URL antes de processar/salvar
            if 'mercadolivre.com' in produto_para_salvar.get('link', '').lower():
                produto_para_salvar['link'] = aplicar_afiliado_ml(produto_para_salvar['link'])

            original_image_url = produto_para_salvar.get('imagem')
            if original_image_url:
                image_bytes = services.processar_imagem_para_quadrado(original_image_url)
                if image_bytes:
                    produto_para_salvar['processed_image_url'] = services.upload_imagem_processada(image_bytes)
            
            # GERAÇÃO DA MENSAGEM COM O NOVO PADRÃO
            mensagem_formatada = formatar_mensagem_marketing(produto_para_salvar)
            
            # SALVAR NO BANCO DE DADOS
            database.salvar_promocao(produto_para_salvar, final_message=mensagem_formatada)

            # RETORNA A MENSAGEM GERADA E A IMAGEM (NÃO CHAMA WEBHOOK)
            return jsonify({
                'success': True, 
                'message': 'Produto processado. Mensagem gerada e salva no banco.', 
                'final_message': mensagem_formatada,
                'image_url': produto_para_salvar.get('processed_image_url') or original_image_url,
            })
        else:
            return jsonify({'error': 'Tipo de processamento inválido'}), 400
        
    except Exception as e:
        final_message_erro = f'Erro interno durante o processamento: {str(e)}'
        if produto_para_salvar:
            database.salvar_promocao(produto_para_salvar, final_message=final_message_erro)
        return jsonify({'error': final_message_erro}), 500

@main_bp.route('/webhook/processar', methods=['POST'])
def processar_produto_webhook():
    """Endpoint para processar produto automaticamente a partir da URL e link de afiliado"""
    try:
        data = request.get_json()
        url_produto = data.get('url_produto', '').strip()
        afiliado_link = data.get('afiliado_link', '').strip()
        
        if not url_produto:
            return jsonify({'error': 'URL do produto é obrigatória'}), 400
        
        # Detectar plataforma automaticamente
        platform = ScraperFactory.detect_platform_from_url(url_produto)
        if not platform:
            return jsonify({'error': 'Plataforma não suportada'}), 400
        
        # Criar scraper
        scraper = ScraperFactory.create_scraper(platform)
        if not scraper:
            return jsonify({'error': f'Scraper não disponível para {platform}'}), 400
        
        # Fazer scraping do produto
        start_time = time.time()
        try:
            produto_dados = scraper.scrape_product(url_produto, afiliado_link)
            response_time = time.time() - start_time
            
            if not produto_dados:
                return jsonify({'error': 'Produto não encontrado ou não foi possível extrair dados'}), 404
            
            # ⭐ Aplica o ID de afiliado na URL antes de processar/salvar
            if 'mercadolivre.com' in produto_dados.get('link', '').lower():
                produto_dados['link'] = aplicar_afiliado_ml(produto_dados['link'])

            # Registrar métricas
            metrics_collector.record_scraping_metric(
                platform=platform,
                operation='webhook_product',
                success=True,
                response_time=response_time,
                products_found=1
            )
            
            # Processar imagem se disponível
            original_image_url = produto_dados.get('imagem')
            if original_image_url:
                try:
                    image_bytes = services.processar_imagem_para_quadrado(original_image_url)
                    if image_bytes:
                        produto_dados['processed_image_url'] = services.upload_imagem_processada(image_bytes)
                except Exception as e:
                    print(f"Erro ao processar imagem: {e}")
            
            # Formatar mensagem de marketing com o NOVO PADRÃO
            mensagem_formatada = formatar_mensagem_marketing(produto_dados)
            
            # Salvar no banco de dados
            database.salvar_promocao(produto_dados, final_message=mensagem_formatada)
            
            return jsonify({
                'success': True,
                'message': 'Produto processado. Mensagem gerada e salva no banco.',
                'produto': produto_dados,
                'final_message': mensagem_formatada,
                'image_url': produto_dados.get('processed_image_url') or original_image_url,
                'platform': platform,
                'response_time': round(response_time, 2)
            })
            
        except Exception as e:
            response_time = time.time() - start_time
            metrics_collector.record_scraping_metric(
                platform=platform,
                operation='webhook_product',
                success=False,
                response_time=response_time,
                error_message=str(e)
            )
            raise
            
    except Exception as e:
        return jsonify({'error': f'Erro ao processar produto: {str(e)}'}), 500

@main_bp.route('/produtos/<string:produto_id>', methods=['DELETE'])
def deletar_produto(produto_id):
    try:
        response = database.deletar_produto_db(produto_id)
        if response.data:
            return jsonify({'success': True, 'message': 'Produto deletado com sucesso!'}), 200
        else:
            return jsonify({'success': False, 'error': 'Produto não encontrado ou não foi possível deletar.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/agendar_produto/<string:produto_id>', methods=['POST'])
def agendar_produto(produto_id):
    try:
        logger.info(f'📅 Recebida requisição de agendamento para produto: {produto_id}')
        data = request.get_json()
        logger.info(f'📦 Dados recebidos: {data}')

        agendamento = data.get('agendamento')
        if not agendamento:
            logger.error('❌ Agendamento não fornecido')
            return jsonify({'error': 'Dados de agendamento são obrigatórios'}), 400

        try:
            naive_dt = datetime.datetime.fromisoformat(agendamento)
            timezone_br = pytz.timezone('America/Sao_Paulo')
            agendamento_dt_br = timezone_br.localize(naive_dt)
            agendamento_dt_utc = agendamento_dt_br.astimezone(pytz.utc)
            agendamento_iso = agendamento_dt_utc.isoformat()
            logger.info(f'⏰ Agendamento convertido: BR={agendamento_dt_br}, UTC={agendamento_iso}')
        except (ValueError, pytz.UnknownTimeZoneError) as ve:
            logger.error(f'❌ Erro ao converter data: {ve}')
            return jsonify({'error': f'Formato de data inválido: {ve}. Use YYYY-MM-DDTHH:MM'}), 400

        logger.info(f'💾 Salvando agendamento no Supabase...')
        response = database.agendar_produto_db(produto_id, agendamento_iso)
        logger.info(f'📊 Resposta do Supabase: {response.data}')

        if response.data and len(response.data) > 0:
            logger.info(f'✅ Produto {produto_id} agendado com sucesso!')
            return jsonify({'success': True, 'message': 'Produto agendado com sucesso!', 'agendamento': agendamento_dt_br.strftime('%Y-%m-%d %H:%M:%S')})
        else:
            logger.error(f'❌ Produto {produto_id} não encontrado no Supabase')
            return jsonify({'success': False, 'error': f'Produto com ID {produto_id} não encontrado.'}), 404
    except Exception as e:
        logger.error(f'❌ Erro interno ao agendar: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/agendar', methods=['POST'])
def agendar_mensagem_whatsapp():
    """Rota para agendar mensagens aprovadas do WhatsApp"""
    try:
        data = request.get_json()

        # Extrair dados da mensagem
        mensagem = data.get('mensagem_customizada', '')
        imagem_url = data.get('imagem_url')
        grupo_origem = data.get('grupo_origem', 'WhatsApp')
        produto_url = data.get('produto_url', '')

        logger.info(f'📱 Recebendo mensagem do WhatsApp para agendamento:')
        logger.info(f'  - Grupo: {grupo_origem}')
        logger.info(f'  - Tem imagem: {bool(imagem_url)}')
        logger.info(f'  - Tamanho mensagem: {len(mensagem)} caracteres')
        logger.info(f'  - Preview: {mensagem[:100]}...' if len(mensagem) > 100 else f'  - Mensagem: {mensagem}')

        # 🔥 SUBSTITUIR LINKS DE AFILIADO AUTOMATICAMENTE
        mensagem_com_afiliado, links_substituidos = substituir_links_afiliado(mensagem)

        if links_substituidos:
            logger.info(f'🔗 Links de afiliado substituídos:')
            for link_info in links_substituidos:
                logger.info(f'  - {link_info["plataforma"]}: {link_info["original"][:50]}... → {link_info["modificada"][:50]}...')
        else:
            logger.info('  - Nenhum link detectado na mensagem')

        # 🖼️ FAZER UPLOAD DA IMAGEM BASE64 PARA SUPABASE
        imagem_url_final = imagem_url
        if imagem_url and imagem_url.startswith('data:image'):
            logger.info('📤 Detectada imagem base64, fazendo upload para Supabase...')
            titulo_simplificado = f"Mensagem do {grupo_origem}"

            # Upload para Supabase
            imagem_url_supabase = database.upload_imagem_whatsapp(imagem_url, titulo_simplificado)

            if imagem_url_supabase:
                imagem_url_final = imagem_url_supabase
                logger.info(f'✅ Imagem do WhatsApp enviada para Supabase: {imagem_url_supabase}')
            else:
                logger.warning('⚠️ Falha no upload da imagem, usando base64 original')

        # Criar objeto de produto para salvar no banco
        produto_dados = {
            "titulo": f"Mensagem do {grupo_origem}",
            "preco_atual": None,
            "preco_original": None,
            "desconto": None,
            "link": produto_url if produto_url else None,
            "afiliado_link": None,
            "imagem": imagem_url_final,  # URL do Supabase (não mais base64)
            "condicao": "whatsapp",
            "vendedor": grupo_origem,
            "disponivel": True,
            "descricao": mensagem_com_afiliado,  # Mensagem COM links de afiliado
            "cupons": [],
            "processed_image_url": imagem_url_final,  # URL do Supabase
            "fonte": "whatsapp"
        }
        
        # Gerar a mensagem final com o NOVO PADRÃO a partir do produto_dados (se houver preço/cupom na mensagem original)
        # Como o whatsapp monitor envia uma mensagem já formatada (e queremos o novo padrão), 
        # vou usar a mensagem_com_afiliado como base para formatar um item para aparecer na lista.

        # Salvar no banco SEM agendamento (para aparecer na lista de "não agendados")
        # A mensagem formatada com quebras de linha E links de afiliado substituídos
        sucesso = database.salvar_promocao(produto_dados, final_message=mensagem_com_afiliado, agendamento_data=None)

        if sucesso:
            logger.info('✅ Mensagem do WhatsApp salva com sucesso no banco!')
            return jsonify({
                'success': True,
                'message': 'Mensagem aprovada e salva para agendamento!',
                'links_substituidos': len(links_substituidos),
                'tem_imagem': bool(imagem_url),
                'plataformas': [link['plataforma'] for link in links_substituidos]
            }), 200
        else:
            logger.error('❌ Falha ao salvar mensagem no banco de dados')
            return jsonify({
                'success': False,
                'error': 'Erro ao salvar mensagem no banco de dados'
            }), 500

    except Exception as e:
        logger.error(f'❌ Erro ao agendar mensagem do WhatsApp: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@main_bp.route('/produtos', methods=['GET'])
def listar_produtos():
    try:
        # Aceitar múltiplos formatos de parâmetros para compatibilidade
        # Formato 1: status/ordem (usado pelo index.html antigo)
        # Formato 2: agendado/order/plataforma (usado pelo WhatsApp Monitor)

        # Determinar formato baseado nos parâmetros recebidos
        if request.args.get('agendado') is not None:
            # Novo formato
            agendado_param = request.args.get('agendado', '').lower()
            if agendado_param == 'true':
                status_filter = 'agendado'
            elif agendado_param == 'false':
                status_filter = 'nao-agendado'
            else:
                status_filter = 'todos'
            ordem_order = request.args.get('order', 'desc')
        else:
            # Formato antigo
            status_filter = request.args.get('status', 'agendado')
            ordem_order = request.args.get('ordem', 'desc')

        plataforma_filter = request.args.get('plataforma', None)

        produtos = database.listar_produtos_db(status_filter, ordem_order)

        # Filtrar por plataforma se especificado
        if plataforma_filter:
            produtos = [p for p in produtos if p.get('plataforma') == plataforma_filter]

        # Converte as datas para o fuso horário de São Paulo para exibição
        for produto in produtos:
            for key in ["agendamento", "created_at"]:
                if produto.get(key) and isinstance(produto[key], str):
                    try:
                        dt_utc = datetime.datetime.fromisoformat(produto[key].replace('Z', '+00:00'))
                        dt_br = dt_utc.astimezone(pytz.timezone('America/Sao_Paulo'))
                        produto[key] = dt_br.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass # Deixa a data como está se houver erro de formato

        return jsonify({'success': True, 'produtos': produtos})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro ao listar produtos do Supabase: {str(e)}'}), 500
    
@main_bp.route('/produtos/<string:produto_id>', methods=['GET'])
def obter_produto(produto_id):
    try:
        produto = database.obter_produto_db(produto_id)
        if produto:
            return jsonify({'success': True, 'produto': produto})
        else:
            return jsonify({'success': False, 'error': 'Produto não encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/produtos/<string:produto_id>', methods=['PUT'])
def editar_produto(produto_id):
    try:
        data = request.get_json()
        dados_atualizacao = {}

        # Coleta todos os campos que podem ser atualizados
        if 'imagem_url' in data:
            original_image_url = data['imagem_url']
            dados_atualizacao['imagem_url'] = original_image_url
            
            # Processar imagem automaticamente para 500x500
            if original_image_url:
                try:
                    image_bytes = services.processar_imagem_para_quadrado(original_image_url)
                    if image_bytes:
                        processed_url = services.upload_imagem_processada(image_bytes)
                        if processed_url:
                            dados_atualizacao['processed_image_url'] = processed_url
                            print(f"✅ Imagem processada automaticamente: {processed_url}")
                except Exception as e:
                    print(f"⚠️ Erro ao processar imagem automaticamente: {e}")
        if 'final_message' in data:
            dados_atualizacao['final_message'] = data['final_message']
        if 'preco_com_cupom' in data:
            dados_atualizacao['preco_com_cupom'] = data['preco_com_cupom']
        if 'cupom_info' in data:
            dados_atualizacao['cupom_info'] = data['cupom_info']

        # Verifica se pelo menos um campo foi enviado para atualização
        if not dados_atualizacao:
            return jsonify({'error': 'Pelo menos um campo deve ser fornecido para edição'}), 400

        # Chama a função do banco de dados para atualizar o produto
        response = database.atualizar_produto_db(produto_id, dados_atualizacao)

        if response.data:
            return jsonify({'success': True, 'message': 'Produto atualizado com sucesso!'})
        else:
            return jsonify({'success': False, 'error': f'Produto com ID {produto_id} não encontrado ou não foi possível atualizar.'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/enviar_produto_agendado/<string:produto_id>', methods=['POST'])
def enviar_produto_agendado(produto_id):
    try:
        data = request.get_json()
        afiliado_link = data.get('afiliado_link', '').strip()
        produto_db = database.obter_produto_db(produto_id)
        if not produto_db:
            return jsonify({'error': 'Produto não encontrado'}), 404
            
        # Priorizar mensagem final salva (se editada)
        if produto_db.get('final_message'):
            mensagem_completa = produto_db.get('final_message')
            image_url_final = produto_db.get('imagem_url') or produto_db.get('processed_image_url')
        else:
            # Recalcular a mensagem com o novo padrão, garantindo que todos os dados sejam passados
            produto_para_formatar = produto_db.copy()
            
            # Se for Mercado Livre, garante o link de afiliado ML
            if 'mercadolivre.com' in produto_para_formatar.get('link_produto', '').lower():
                produto_para_formatar['link_produto'] = aplicar_afiliado_ml(produto_para_formatar.get('link_produto', ''))
                # Atualiza também o campo de link de afiliado para o formatador
                produto_para_formatar['afiliado_link'] = produto_para_formatar.get('link_produto') 
            
            produto_para_formatar['afiliado_link'] = afiliado_link or produto_para_formatar.get('afiliado_link')
            produto_para_formatar['link'] = produto_para_formatar.get('link_produto') # Garantir link
            
            mensagem_completa = formatar_mensagem_marketing(produto_para_formatar)
            image_url_final = produto_db.get('imagem_url') or produto_db.get('processed_image_url')

        # RETORNA A MENSAGEM GERADA E A IMAGEM (NÃO CHAMA WEBHOOK)
        return jsonify({
            'success': True, 
            'message': 'Mensagem gerada com sucesso e pronta para envio!', 
            'final_message': mensagem_completa.strip(),
            'image_url': image_url_final
        })
            
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/storage/imagens', methods=['GET'])
def listar_imagens():
    try:
        bucket_name = request.args.get('bucket', os.getenv('SUPABASE_BUCKET_NAME', 'imagens_melhoradas_tech'))
        pasta = request.args.get('pasta', '')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        search_term = request.args.get('search', '')
        imagens = database.listar_imagens_bucket(
            bucket_name=bucket_name, pasta=pasta, limit=limit,
            offset=offset, search_term=search_term
        )
        return jsonify({'success': True, 'imagens': imagens})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro ao listar imagens: {str(e)}'}), 500

@main_bp.route('/storage/pastas', methods=['GET'])
def listar_pastas():
    try:
        bucket_name = request.args.get('bucket', os.getenv('SUPABASE_BUCKET_NAME', 'imagens_melhoradas_tech'))
        pasta_pai = request.args.get('pasta_pai', '')
        
        pastas = database.listar_pastas_bucket(
            bucket_name=bucket_name,
            pasta_pai=pasta_pai
        )
        
        return jsonify({
            'success': True,
            'pastas': pastas
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro ao listar pastas: {str(e)}'}), 500

@main_bp.route('/storage/url_publica', methods=['POST'])
def obter_url_publica():
    try:
        data = request.get_json()
        bucket_name = data.get('bucket', os.getenv('SUPABASE_BUCKET_NAME', 'imagens_melhoradas_tech'))
        caminho_arquivo = data.get('caminho', '')
        
        if not caminho_arquivo:
            return jsonify({'success': False, 'error': 'Caminho do arquivo é obrigatório'}), 400
        
        url = database.obter_url_publica_imagem(
            bucket_name=bucket_name,
            caminho_arquivo=caminho_arquivo
        )
        
        if url:
            return jsonify({'success': True, 'url': url})
        else:
            return jsonify({'success': False, 'error': 'Não foi possível obter a URL'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro ao obter URL: {str(e)}'}), 500

# === NOVAS ROTAS DO SISTEMA UNIFICADO ===

@main_bp.route('/scrape/unified', methods=['POST'])
def scrape_unified():
    """Endpoint unificado para scraping de qualquer plataforma"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        affiliate_link = data.get('affiliate_link', '').strip()
        
        if not url:
            return jsonify({'error': 'URL é obrigatória'}), 400
        
        # Detectar plataforma automaticamente
        platform = ScraperFactory.detect_platform_from_url(url)
        if not platform:
            return jsonify({'error': 'Plataforma não suportada'}), 400
        
        # Criar scraper
        scraper = ScraperFactory.create_scraper(platform)
        if not scraper:
            return jsonify({'error': f'Scraper não disponível para {platform}'}), 400
        
        # Fazer scraping
        start_time = time.time()
        try:
            product_data = scraper.scrape_product(url, affiliate_link)
            response_time = time.time() - start_time
            
            if product_data:
                # ⭐ Aplica o ID de afiliado na URL para a resposta de sucesso
                if 'mercadolivre.com' in product_data.get('link', '').lower():
                    product_data['link'] = aplicar_afiliado_ml(product_data['link'])

                # Registrar métricas
                metrics_collector.record_scraping_metric(
                    platform=platform,
                    operation='product',
                    success=True,
                    response_time=response_time,
                    products_found=1
                )
                
                return jsonify({
                    'success': True,
                    'product': product_data,
                    'platform': platform,
                    'response_time': round(response_time, 2)
                })
            else:
                # Registrar falha
                metrics_collector.record_scraping_metric(
                    platform=platform,
                    operation='product',
                    success=False,
                    response_time=response_time,
                    error_message='Produto não encontrado'
                )
                
                return jsonify({'error': 'Produto não encontrado'}), 404
                
        except Exception as e:
            response_time = time.time() - start_time
            metrics_collector.record_scraping_metric(
                platform=platform,
                operation='product',
                success=False,
                response_time=response_time,
                error_message=str(e)
            )
            raise
            
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/scrape/search', methods=['POST'])
def search_unified():
    """Endpoint unificado para busca em qualquer plataforma"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        platform = data.get('platform', 'todas')
        max_pages = data.get('max_pages', 2)
        
        if not query:
            return jsonify({'error': 'Query é obrigatória'}), 400
        
        products = []
        
        if platform == 'todas':
            # Buscar em todas as plataformas
            available_platforms = ScraperFactory.get_available_platforms()
            for platform_name in available_platforms:
                try:
                    scraper = ScraperFactory.create_scraper(platform_name)
                    if scraper:
                        start_time = time.time()
                        platform_products = scraper.scrape_search(query, max_pages)
                        response_time = time.time() - start_time
                        
                        # ⭐ Aplica o ID de afiliado na URL dos resultados
                        if platform_name.lower() == 'mercadolivre':
                             for p in platform_products:
                                 p['link'] = aplicar_afiliado_ml(p['link'])
                        
                        # Registrar métricas
                        metrics_collector.record_scraping_metric(
                            platform=platform_name,
                            operation='search',
                            success=True,
                            response_time=response_time,
                            products_found=len(platform_products)
                        )
                        
                        products.extend(platform_products)
                        
                except Exception as e:
                    metrics_collector.record_scraping_metric(
                        platform=platform_name,
                        operation='search',
                        success=False,
                        response_time=0,
                        error_message=str(e)
                    )
                    continue
        else:
            # Buscar em plataforma específica
            scraper = ScraperFactory.create_scraper(platform)
            if not scraper:
                return jsonify({'error': f'Plataforma {platform} não suportada'}), 400
            
            start_time = time.time()
            products = scraper.scrape_search(query, max_pages)
            response_time = time.time() - start_time

            # ⭐ Aplica o ID de afiliado na URL dos resultados
            if platform.lower() == 'mercadolivre':
                for p in products:
                    p['link'] = aplicar_afiliado_ml(p['link'])
            
            # Registrar métricas
            metrics_collector.record_scraping_metric(
                platform=platform,
                operation='search',
                success=True,
                response_time=response_time,
                products_found=len(products)
            )
        
        return jsonify({
            'success': True,
            'products': products,
            'total': len(products),
            'platform': platform
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/queue/add', methods=['POST'])
def add_to_queue():
    """Adiciona produto à fila de processamento"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        affiliate_link = data.get('affiliate_link', '').strip()
        priority = data.get('priority', 0)
        
        if not url:
            return jsonify({'error': 'URL é obrigatória'}), 400
        
        # Detectar plataforma
        platform = ScraperFactory.detect_platform_from_url(url)
        if not platform:
            return jsonify({'error': 'Plataforma não suportada'}), 400
        
        # Adicionar à fila
        task_id = queue_manager.add_task(url, affiliate_link, platform, priority)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'platform': platform,
            'message': 'Produto adicionado à fila'
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/queue/status', methods=['GET'])
def queue_status():
    """Retorna status da fila"""
    try:
        status = queue_manager.get_queue_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/queue/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Retorna status de uma tarefa específica"""
    try:
        task = queue_manager.get_task(task_id)
        if not task:
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        
        return jsonify({'success': True, 'task': task.to_dict()})
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/queue/task/<task_id>', methods=['DELETE'])
def cancel_task(task_id):
    """Cancela uma tarefa"""
    try:
        success = queue_manager.cancel_task(task_id)
        if success:
            return jsonify({'success': True, 'message': 'Tarefa cancelada'})
        else:
            return jsonify({'error': 'Tarefa não encontrada ou não pode ser cancelada'}), 404
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/monitoring/stats', methods=['GET'])
def get_monitoring_stats():
    """Retorna estatísticas de monitoramento"""
    try:
        stats = metrics_collector.get_stats_summary()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/monitoring/health', methods=['GET'])
def get_health_status():
    """Retorna status de saúde do sistema"""
    try:
        health = health_checker.check_health()
        return jsonify({'success': True, 'health': health})
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/monitoring/alerts', methods=['GET'])
def get_alerts():
    """Retorna alertas ativos"""
    try:
        alerts = alert_manager.check_alerts()
        return jsonify({'success': True, 'alerts': alerts})
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/monitoring/platform/<platform>', methods=['GET'])
def get_platform_stats(platform):
    """Retorna estatísticas de uma plataforma específica"""
    try:
        stats = metrics_collector.get_platform_stats(platform)
        return jsonify({'success': True, 'platform': platform, 'stats': stats})
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/cache/stats', methods=['GET'])
def get_cache_stats():
    """Retorna estatísticas do cache"""
    try:
        stats = cache_manager.get_stats()
        memory_usage = cache_manager.get_memory_usage()
        return jsonify({
            'success': True,
            'cache_stats': stats,
            'memory_usage': memory_usage
        })
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@main_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Limpa o cache"""
    try:
        cache_manager.clear()
        return jsonify({'success': True, 'message': 'Cache limpo com sucesso'})
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

# === ROTAS DO WHATSAPP MONITOR (BAILEYS PROXY) ===

@main_bp.route('/whatsapp/send', methods=['POST'])
def send_whatsapp_message():
    """
    Endpoint para enviar a mensagem formatada para o serviço Baileys/WhatsApp Monitor.
    Recebe message e image_url geradas no processamento.
    """
    try:
        data = request.get_json()
        message = data.get('message')
        image_url = data.get('imageUrl')
        
        # Define o grupo alvo a partir do env ou usa um placeholder
        target_group = data.get('targetGroup') or os.getenv('WHATSAPP_DEFAULT_GROUP', '120363420970681294@g.us')

        if not message:
            return jsonify({'success': False, 'error': 'Mensagem é obrigatória'}), 400

        # Payload para o serviço Baileys (O endpoint do monitor pode ter um /send-message)
        baileys_payload = {
            'target': target_group, 
            'text': message,
            'imageUrl': image_url 
        }
        
        # Endpoint no serviço Baileys (Monitor)
        # Assumindo que o serviço Baileys/Monitor tem um endpoint /send-message
        baileys_url = f'{WHATSAPP_MONITOR_URL}/send-message' 

        logger.info(f'📱 Enviando mensagem via Baileys para {target_group}...')
        
        # Faz o proxy da requisição
        response = requests.post(baileys_url, json=baileys_payload, timeout=10)

        # Retorna a resposta do serviço Baileys
        # Se o Baileys retornar JSON:
        try:
            baileys_response_json = response.json()
        except requests.exceptions.JSONDecodeError:
            baileys_response_json = {'error': response.text}
            
        if response.status_code in [200, 201, 202]:
             return jsonify({
                'success': True,
                'message': 'Mensagem enviada com sucesso para o WhatsApp!',
                'baileys_response': baileys_response_json
             }), 200
        else:
             return jsonify({
                'success': False,
                'error': 'Falha ao enviar mensagem via Baileys',
                'status_code': response.status_code,
                'baileys_response': baileys_response_json
             }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Timeout ao tentar conectar com o serviço WhatsApp Monitor (Baileys)'}), 503
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Serviço WhatsApp Monitor (Baileys) indisponível. Verifique se o serviço está online.'}), 503
    except Exception as e:
        logger.error(f'❌ Erro interno no envio via WhatsApp: {str(e)}')
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500


@main_bp.route('/whatsapp-monitor')
@login_required
def whatsapp_monitor():
    """Página de monitoramento de grupos do WhatsApp"""
    return render_template('whatsapp_monitor.html')

@main_bp.route('/whatsapp/status', methods=['GET'])
def whatsapp_status():
    """Proxy para status do WhatsApp"""
    try:
        response = requests.get(f'{WHATSAPP_MONITOR_URL}/status', timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': f'WhatsApp Monitor não está rodando: {str(e)}'}), 503

@main_bp.route('/whatsapp/qr', methods=['GET'])
def whatsapp_qr():
    """Proxy para QR Code do WhatsApp"""
    try:
        # WHATSAPP_MONITOR_URL vem da variável de ambiente
        response = requests.get(f'{WHATSAPP_MONITOR_URL}/qr', timeout=5)
        
        # Tenta ler o JSON (o erro 'Unexpected token <' foi causado por um erro 404/500 no Flask)
        return jsonify(response.json()) 

    except Exception as e:
        # Se você ainda receber o erro 'Expecting value', significa que o JSON está quebrado
        return jsonify({'error': f'Erro ao obter QR Code: {str(e)}'}), 503

@main_bp.route('/whatsapp/groups', methods=['GET'])
def whatsapp_groups():
    """Proxy para listar grupos do WhatsApp (Mais robusto)"""
    try:
        # AUMENTAR O TIMEOUT (como sugerido)
        response = requests.get(f'{WHATSAPP_MONITOR_URL}/groups', timeout=30) 
        
        # TENTA LER O JSON
        try:
            return jsonify(response.json())
        except requests.exceptions.JSONDecodeError as json_error:
            # SE FALHAR, RETORNA O CONTEÚDO CRU QUE QUEBROU
            error_details = {
                'error': 'Falha na decodificação JSON do Monitor',
                'details': str(json_error),
                'status_code': response.status_code,
                # Retorna os primeiros 500 caracteres da resposta para diagnóstico
                'raw_response_start': response.text[:500] 
            }
            # Loga a resposta completa no servidor
            logger.error(f"Erro JSON na rota groups. Resposta crua: {response.text}") 
            return jsonify(error_details), 503
            
    except Exception as e:
        return jsonify({'error': f'Erro ao listar grupos: {str(e)}'}), 503

@main_bp.route('/whatsapp/monitor', methods=['POST'])
def whatsapp_monitor_group():
    """Proxy para adicionar grupo ao monitoramento (rota que o JS chama)"""
    try:
        data = request.get_json()

        # Verificar se WhatsApp está conectado antes de tentar adicionar grupo
        try:
            status_response = requests.get(f'{WHATSAPP_MONITOR_URL}/status', timeout=5)
            status_data = status_response.json()
            if not status_data.get('connected', False):
                return jsonify({'success': False, 'error': 'WhatsApp não está conectado. Escaneie o QR Code primeiro.'}), 400
        except:
            pass  # Continua mesmo se não conseguir verificar status

        # Proxy para o serviço Node.js
        response = requests.post(f'{WHATSAPP_MONITOR_URL}/monitor', json=data, timeout=10)

        # Verificar se a resposta é JSON válido
        if response.status_code == 200:
            try:
                return jsonify(response.json())
            except requests.exceptions.JSONDecodeError:
                logger.error(f'Resposta não é JSON válido: {response.text[:500]}')
                return jsonify({'success': False, 'error': 'Resposta inválida do WhatsApp Monitor'}), 503
        else:
            logger.error(f'Erro HTTP {response.status_code}: {response.text[:500]}')
            return jsonify({'success': False, 'error': f'Erro HTTP {response.status_code}'}), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Timeout ao conectar com WhatsApp Monitor'}), 503
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'WhatsApp Monitor não está acessível'}), 503
    except Exception as e:
        logger.error(f'Erro ao adicionar grupo: {str(e)}')
        return jsonify({'success': False, 'error': f'Erro ao adicionar grupo: {str(e)}'}), 503

@main_bp.route('/whatsapp/unmonitor', methods=['POST'])
def whatsapp_unmonitor():
    """Proxy para remover grupo do monitoramento (rota que o JS chama)"""
    try:
        data = request.get_json()
        group_id = data.get('groupId')

        if not group_id:
            return jsonify({'success': False, 'error': 'ID do grupo ausente'}), 400

        # Proxy para o serviço Node.js
        response = requests.post(f'{WHATSAPP_MONITOR_URL}/unmonitor', json={'groupId': group_id}, timeout=10)

        # Verificar se a resposta é JSON válido
        if response.status_code in [200, 404]:
            try:
                return jsonify(response.json())
            except requests.exceptions.JSONDecodeError:
                logger.error(f'Resposta não é JSON válido: {response.text[:500]}')
                return jsonify({'success': False, 'error': 'Resposta inválida do WhatsApp Monitor'}), 503
        else:
            logger.error(f'Erro HTTP {response.status_code}: {response.text[:500]}')
            return jsonify({'success': False, 'error': f'Erro HTTP {response.status_code}'}), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Timeout ao conectar com WhatsApp Monitor'}), 503
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'WhatsApp Monitor não está acessível'}), 503
    except Exception as e:
        logger.error(f'Erro ao remover grupo: {str(e)}')
        return jsonify({'success': False, 'error': f'Erro ao remover grupo: {str(e)}'}), 503

@main_bp.route('/whatsapp/messages', methods=['GET'])
def whatsapp_messages():
    """Proxy para obter mensagens capturadas"""
    try:
        limit = request.args.get('limit', 100)
        response = requests.get(f'{WHATSAPP_MONITOR_URL}/messages?limit={limit}', timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': f'Erro ao obter mensagens: {str(e)}'}), 503

@main_bp.route('/whatsapp/logout', methods=['POST'])
def whatsapp_logout():
    """Proxy para fazer logout do WhatsApp"""
    try:
        # O valor de WHATSAPP_MONITOR_URL já foi corrigido no topo do arquivo.
        WHATSAPP_URL = os.getenv('WHATSAPP_MONITOR_URL', 'http://localhost:3001')

        # Constrói a URL de forma segura (garantindo o scheme 'http://')
        full_url = f'{WHATSAPP_URL}/logout'

        response = requests.post(full_url, timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': f'Erro ao fazer logout: {str(e)}'}), 503

@main_bp.route('/whatsapp/affiliate/settings', methods=['GET'])
def whatsapp_get_affiliate_settings():
    """Proxy para obter configurações de afiliado"""
    try:
        response = requests.get(f'{WHATSAPP_MONITOR_URL}/affiliate/settings', timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': f'Erro ao obter configurações: {str(e)}'}), 503

@main_bp.route('/whatsapp/affiliate/settings', methods=['POST'])
def whatsapp_set_affiliate_settings():
    """Proxy para configurar link de afiliado"""
    try:
        data = request.get_json()
        response = requests.post(f'{WHATSAPP_MONITOR_URL}/affiliate/settings', json=data, timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': f'Erro ao salvar configuração: {str(e)}'}), 503

@main_bp.route('/whatsapp/affiliate/settings/<platform>', methods=['DELETE'])
def whatsapp_delete_affiliate_settings(platform):
    """Proxy para deletar configuração de afiliado"""
    try:
        response = requests.delete(f'{WHATSAPP_MONITOR_URL}/affiliate/settings/{platform}', timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': f'Erro ao deletar configuração: {str(e)}'}), 503

@main_bp.route('/upload-image', methods=['POST'])
def upload_image():
    """
    Endpoint para fazer upload de imagens coladas/selecionadas do modal de edição.
    Recebe imagem em base64 e faz upload para o Supabase Storage.
    """
    try:
        data = request.get_json()
        base64_image = data.get('image', '')
        filename = data.get('filename', 'pasted-image.png')

        if not base64_image:
            return jsonify({'success': False, 'error': 'Imagem não fornecida'}), 400

        logger.info(f'📤 Recebendo upload de imagem: {filename}')

        # Usar a função existente para upload de imagem do WhatsApp
        # (ela já suporta base64)
        titulo_produto = f"Edição Manual - {filename}"
        public_url = database.upload_imagem_whatsapp(base64_image, titulo_produto)

        if public_url:
            logger.info(f'✅ Upload concluído: {public_url}')
            return jsonify({
                'success': True,
                'url': public_url,
                'message': 'Imagem enviada com sucesso!'
            })
        else:
            logger.error('❌ Falha no upload da imagem')
            return jsonify({
                'success': False,
                'error': 'Erro ao fazer upload da imagem para o Supabase'
            }), 500

    except Exception as e:
        logger.error(f'❌ Erro no endpoint de upload: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

# === ROTAS DE ENVIO DE MENSAGENS ===

@main_bp.route('/enviar-mensagem', methods=['POST'])
def enviar_mensagem_manual():
    """Envia mensagem manualmente para grupos selecionados"""
    try:
        from .scheduler import message_scheduler

        data = request.get_json()
        produto_id = data.get('produto_id')
        grupos = data.get('grupos', [])

        if not produto_id:
            return jsonify({'success': False, 'error': 'produto_id é obrigatório'}), 400

        if not grupos or not isinstance(grupos, list):
            return jsonify({'success': False, 'error': 'grupos deve ser uma lista não vazia'}), 400

        logger.info(f'📤 Enviando mensagem manual do produto {produto_id} para {len(grupos)} grupo(s)')

        # Enviar mensagem
        resultado = message_scheduler.send_message_now(produto_id, grupos)

        if resultado['success']:
            return jsonify({
                'success': True,
                'message': f'Mensagem enviada para {resultado["total_enviado"]} grupo(s)',
                'detalhes': resultado
            })
        else:
            return jsonify({
                'success': False,
                'error': resultado.get('error', 'Erro desconhecido')
            }), 500

    except Exception as e:
        logger.error(f'❌ Erro ao enviar mensagem: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/scheduler/status', methods=['GET'])
def scheduler_status():
    """Retorna status do scheduler de mensagens"""
    try:
        from .scheduler import message_scheduler

        return jsonify({
            'success': True,
            'running': message_scheduler.running,
            'check_interval': message_scheduler.check_interval,
            'whatsapp_url': message_scheduler.whatsapp_url
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/configurar-grupos-auto', methods=['POST'])
def configurar_grupos_auto():
    """Configura quais grupos recebem mensagens agendadas automaticamente"""
    try:
        data = request.get_json()
        grupos = data.get('grupos', [])

        if not isinstance(grupos, list):
            return jsonify({'success': False, 'error': 'grupos deve ser uma lista'}), 400

        # Salvar configuração no .env ou banco de dados
        # Por enquanto, vamos salvar em um arquivo JSON
        import json
        config_file = 'app/config/auto_send_groups.json'

        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({'grupos': grupos}, f, indent=2)

        logger.info(f'✅ Configurados {len(grupos)} grupos para envio automático')

        return jsonify({
            'success': True,
            'message': f'{len(grupos)} grupo(s) configurado(s) para envio automático'
        })

    except Exception as e:
        logger.error(f'❌ Erro ao configurar grupos: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/configurar-grupos-auto', methods=['GET'])
def obter_grupos_auto():
    """Obtém configuração de grupos para envio automático"""
    try:
        import json
        config_file = 'app/config/auto_send_groups.json'

        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return jsonify({
                    'success': True,
                    'grupos': config.get('grupos', [])
                })
        else:
            return jsonify({
                'success': True,
                'grupos': []
            })

    except Exception as e:
        logger.error(f'❌ Erro ao obter grupos: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ROTAS PARA GERENCIAR GRUPOS FIXOS DE AGENDAMENTO
# ============================================================================

@main_bp.route('/grupos-fixos', methods=['GET'])
def listar_grupos_fixos_route():
    """Lista todos os grupos fixos cadastrados."""
    try:
        grupos = database.listar_grupos_fixos()
        return jsonify({
            'success': True,
            'grupos': grupos
        })
    except Exception as e:
        print(f'Erro ao listar grupos fixos: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/grupos-fixos', methods=['POST'])
def adicionar_grupo_fixo_route():
    """Adiciona um novo grupo fixo."""
    try:
        data = request.get_json()
        grupo_id = data.get('grupo_id')
        grupo_nome = data.get('grupo_nome')

        if not grupo_id or not grupo_nome:
            return jsonify({'success': False, 'error': 'grupo_id e grupo_nome são obrigatórios'}), 400

        resultado = database.adicionar_grupo_fixo(grupo_id, grupo_nome)

        if resultado['success']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400

    except Exception as e:
        print(f'Erro ao adicionar grupo fixo: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/grupos-fixos/<string:grupo_id>', methods=['DELETE'])
def remover_grupo_fixo_route(grupo_id):
    """Remove um grupo fixo."""
    try:
        resultado = database.remover_grupo_fixo(grupo_id)

        if resultado['success']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400

    except Exception as e:
        print(f'Erro ao remover grupo fixo: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/grupos-fixos/<string:grupo_id>/toggle', methods=['PUT'])
def alternar_status_grupo_fixo_route(grupo_id):
    """Ativa ou desativa um grupo fixo."""
    try:
        data = request.get_json()
        ativo = data.get('ativo', True)

        resultado = database.alternar_status_grupo_fixo(grupo_id, ativo)

        if resultado['success']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400

    except Exception as e:
        print(f'Erro ao alternar status do grupo fixo: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ROTAS DE GERENCIAMENTO DE CUPONS
# ============================================================================

@main_bp.route('/cupons', methods=['GET'])
@login_required
def listar_cupons_route():
    """Lista todos os cupons cadastrados."""
    try:
        cupons = database.listar_cupons()
        return jsonify({
            'success': True,
            'cupons': cupons
        })
    except Exception as e:
        print(f'Erro ao listar cupons: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/cupons', methods=['POST'])
@login_required
def adicionar_cupom_route():
    """Adiciona um novo cupom."""
    try:
        data = request.get_json()
        codigo = data.get('codigo')
        porcentagem = data.get('porcentagem')
        limite_valor = data.get('limite_valor')

        if not codigo or porcentagem is None or limite_valor is None:
            return jsonify({'success': False, 'error': 'codigo, porcentagem e limite_valor são obrigatórios'}), 400

        resultado = database.adicionar_cupom(codigo, porcentagem, limite_valor)

        if resultado['success']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400

    except Exception as e:
        print(f'Erro ao adicionar cupom: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/cupons/<int:cupom_id>', methods=['PUT'])
@login_required
def atualizar_cupom_route(cupom_id):
    """Atualiza um cupom existente."""
    try:
        data = request.get_json()
        codigo = data.get('codigo')
        porcentagem = data.get('porcentagem')
        limite_valor = data.get('limite_valor')

        if not codigo or porcentagem is None or limite_valor is None:
            return jsonify({'success': False, 'error': 'codigo, porcentagem e limite_valor são obrigatórios'}), 400

        resultado = database.atualizar_cupom(cupom_id, codigo, porcentagem, limite_valor)

        if resultado['success']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400

    except Exception as e:
        print(f'Erro ao atualizar cupom: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/cupons/<int:cupom_id>', methods=['DELETE'])
@login_required
def remover_cupom_route(cupom_id):
    """Remove um cupom."""
    try:
        resultado = database.remover_cupom(cupom_id)

        if resultado['success']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400

    except Exception as e:
        print(f'Erro ao remover cupom: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/cupons/<int:cupom_id>/toggle', methods=['PUT'])
@login_required
def alternar_status_cupom_route(cupom_id):
    """Ativa ou desativa um cupom."""
    try:
        data = request.get_json()
        ativo = data.get('ativo', True)

        resultado = database.alternar_status_cupom(cupom_id, ativo)

        if resultado['success']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400

    except Exception as e:
        print(f'Erro ao alternar status do cupom: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/cupons/ativos', methods=['GET'])
@login_required
def listar_cupons_ativos_route():
    """Lista apenas cupons ativos."""
    try:
        cupons = database.listar_cupons_ativos()
        return jsonify({
            'success': True,
            'cupons': cupons
        })
    except Exception as e:
        print(f'Erro ao listar cupons ativos: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/cupons/calcular', methods=['POST'])
@login_required
def calcular_valor_com_cupom_route():
    """Calcula valor final com cupom aplicado."""
    try:
        data = request.get_json()
        preco_original = data.get('preco_original')
        cupom_id = data.get('cupom_id')

        if preco_original is None or cupom_id is None:
            return jsonify({'success': False, 'error': 'preco_original e cupom_id são obrigatórios'}), 400

        resultado = database.calcular_valor_com_cupom(float(preco_original), cupom_id)
        return jsonify(resultado)

    except Exception as e:
        print(f'Erro ao calcular valor com cupom: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROTAS PARA CLONAGEM DE MENSAGENS COM AFILIADO E ENVIO ESPAÇADO
# ============================================================================

@main_bp.route('/whatsapp/clone-message', methods=['POST'])
@login_required
def clone_message_with_affiliate():
    """
    Clona uma mensagem, substitui links por afiliados e agenda para envio espaçado.

    Recebe:
    {
        'mensagem': str,
        'imagem_url': str (opcional),
        'grupo_origem': str,
        'grupo_origem_nome': str
    }

    Retorna:
    {
        'success': True,
        'mensagem_original': str,
        'mensagem_com_afiliado': str,
        'links_substituidos': [...],
        'agendamento': str (ISO datetime)
    }
    """
    try:
        data = request.get_json()

        mensagem = data.get('mensagem', '').strip()
        imagem_url = data.get('imagem_url')
        grupo_origem = data.get('grupo_origem', '')
        grupo_origem_nome = data.get('grupo_origem_nome', 'Grupo desconhecido')

        if not mensagem:
            return jsonify({'success': False, 'error': 'Mensagem é obrigatória'}), 400

        logger.info(f'📥 Clonando mensagem do grupo: {grupo_origem_nome}')
        logger.info(f'   Tamanho: {len(mensagem)} caracteres')

        # 1. Substituir links por afiliados
        mensagem_com_afiliado, links_substituidos = substituir_links_afiliado(mensagem)

        if links_substituidos:
            logger.info(f'🔗 {len(links_substituidos)} link(s) substituído(s):')
            for link_info in links_substituidos:
                logger.info(f'   - {link_info["plataforma"]}')
        else:
            logger.info('   Nenhum link de produto detectado')

        # 2. Upload da imagem se for base64
        imagem_url_final = imagem_url
        if imagem_url and imagem_url.startswith('data:image'):
            logger.info('📤 Fazendo upload de imagem base64...')
            imagem_url_supabase = database.upload_imagem_whatsapp(imagem_url, f"Clone de {grupo_origem_nome}")
            if imagem_url_supabase:
                imagem_url_final = imagem_url_supabase
                logger.info(f'✅ Imagem enviada: {imagem_url_supabase[:80]}...')

        # 3. Adicionar à fila de envio (intervalo automático de 5 min)
        resultado_fila = database.adicionar_mensagem_fila({
            'mensagem_original': mensagem,
            'mensagem_com_afiliado': mensagem_com_afiliado,
            'imagem_url': imagem_url_final,
            'grupo_origem': grupo_origem,
            'grupo_origem_nome': grupo_origem_nome
        })

        if not resultado_fila['success']:
            return jsonify({
                'success': False,
                'error': f'Erro ao adicionar à fila: {resultado_fila.get("error", "Erro desconhecido")}'
            }), 500

        logger.info(f'✅ Mensagem clonada e agendada para: {resultado_fila.get("agendamento")}')

        return jsonify({
            'success': True,
            'mensagem_original': mensagem,
            'mensagem_com_afiliado': mensagem_com_afiliado,
            'links_substituidos': links_substituidos,
            'imagem_url': imagem_url_final,
            'agendamento': resultado_fila.get('agendamento'),
            'message': f'Mensagem clonada! Envio agendado para {resultado_fila.get("agendamento")}'
        })

    except Exception as e:
        logger.error(f'❌ Erro ao clonar mensagem: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/whatsapp/clone-multiple', methods=['POST'])
@login_required
def clone_multiple_messages():
    """
    Clona múltiplas mensagens de uma vez (seleção em lote).

    Recebe:
    {
        'mensagens': [
            {'mensagem': str, 'imagem_url': str, 'grupo_origem': str, 'grupo_origem_nome': str},
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        mensagens = data.get('mensagens', [])

        if not mensagens:
            return jsonify({'success': False, 'error': 'Nenhuma mensagem fornecida'}), 400

        resultados = []
        total_sucesso = 0
        total_erro = 0

        for msg in mensagens:
            try:
                mensagem = msg.get('mensagem', '').strip()
                if not mensagem:
                    continue

                # Substituir links
                mensagem_com_afiliado, links_substituidos = substituir_links_afiliado(mensagem)

                # Upload de imagem se necessário
                imagem_url = msg.get('imagem_url')
                if imagem_url and imagem_url.startswith('data:image'):
                    imagem_url = database.upload_imagem_whatsapp(imagem_url, f"Clone lote")

                # Adicionar à fila
                resultado = database.adicionar_mensagem_fila({
                    'mensagem_original': mensagem,
                    'mensagem_com_afiliado': mensagem_com_afiliado,
                    'imagem_url': imagem_url,
                    'grupo_origem': msg.get('grupo_origem', ''),
                    'grupo_origem_nome': msg.get('grupo_origem_nome', '')
                })

                if resultado['success']:
                    total_sucesso += 1
                    resultados.append({
                        'sucesso': True,
                        'agendamento': resultado.get('agendamento'),
                        'links_substituidos': len(links_substituidos)
                    })
                else:
                    total_erro += 1
                    resultados.append({'sucesso': False, 'erro': resultado.get('error')})

            except Exception as e:
                total_erro += 1
                resultados.append({'sucesso': False, 'erro': str(e)})

        logger.info(f'📋 Clonagem em lote: {total_sucesso} sucesso, {total_erro} erro')

        return jsonify({
            'success': True,
            'total_processado': len(mensagens),
            'total_sucesso': total_sucesso,
            'total_erro': total_erro,
            'resultados': resultados
        })

    except Exception as e:
        logger.error(f'❌ Erro na clonagem em lote: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/fila-mensagens', methods=['GET'])
@login_required
def listar_fila_mensagens_route():
    """Lista mensagens na fila de envio."""
    try:
        status = request.args.get('status', 'todos')
        limit = int(request.args.get('limit', 100))

        mensagens = database.listar_fila_mensagens(status, limit)

        # Converter datas para fuso horário de SP
        for msg in mensagens:
            for key in ['agendamento_envio', 'criado_em', 'enviado_em']:
                if msg.get(key):
                    try:
                        dt_utc = datetime.datetime.fromisoformat(msg[key].replace('Z', '+00:00'))
                        dt_br = dt_utc.astimezone(pytz.timezone('America/Sao_Paulo'))
                        msg[key] = dt_br.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass

        return jsonify({
            'success': True,
            'mensagens': mensagens,
            'total': len(mensagens)
        })

    except Exception as e:
        logger.error(f'❌ Erro ao listar fila: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/fila-mensagens/estatisticas', methods=['GET'])
@login_required
def estatisticas_fila_route():
    """Retorna estatísticas da fila de mensagens."""
    try:
        stats = database.obter_estatisticas_fila()

        # Converter próximo envio para horário de SP
        if stats.get('proximo_envio'):
            try:
                dt_utc = datetime.datetime.fromisoformat(stats['proximo_envio'].replace('Z', '+00:00'))
                dt_br = dt_utc.astimezone(pytz.timezone('America/Sao_Paulo'))
                stats['proximo_envio'] = dt_br.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass

        return jsonify({'success': True, **stats})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/fila-mensagens/<int:mensagem_id>', methods=['DELETE'])
@login_required
def deletar_mensagem_fila_route(mensagem_id):
    """Remove uma mensagem da fila."""
    try:
        resultado = database.deletar_mensagem_fila(mensagem_id)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/fila-mensagens/limpar', methods=['POST'])
@login_required
def limpar_fila_route():
    """Limpa mensagens enviadas antigas."""
    try:
        data = request.get_json() or {}
        dias = data.get('dias', 7)

        resultado = database.limpar_fila_enviadas(dias)
        return jsonify(resultado)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/fila-mensagens/processar-agora', methods=['POST'])
@login_required
def processar_fila_agora_route():
    """Força processamento imediato da fila."""
    try:
        from .scheduler import clone_queue_scheduler

        resultado = clone_queue_scheduler.process_queue_now()
        return jsonify(resultado)

    except Exception as e:
        logger.error(f'❌ Erro ao processar fila: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/fila-mensagens/configurar-intervalo', methods=['POST'])
@login_required
def configurar_intervalo_fila_route():
    """Configura o intervalo entre envios (em minutos)."""
    try:
        data = request.get_json()
        intervalo = data.get('intervalo_minutos', 5)

        if intervalo < 1:
            return jsonify({'success': False, 'error': 'Intervalo mínimo é 1 minuto'}), 400

        if intervalo > 60:
            return jsonify({'success': False, 'error': 'Intervalo máximo é 60 minutos'}), 400

        # Salvar configuração
        import json
        config_file = 'app/config/clone_queue_config.json'
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        with open(config_file, 'w') as f:
            json.dump({'intervalo_minutos': intervalo}, f)

        logger.info(f'⚙️ Intervalo de envio configurado para {intervalo} minutos')

        return jsonify({
            'success': True,
            'message': f'Intervalo configurado para {intervalo} minutos'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/whatsapp/clone-page')
@login_required
def clone_page():
    """Página de clonagem de mensagens"""
    return render_template('clone_messages.html')