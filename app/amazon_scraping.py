# /Promo-Brothers-Scraper/app/amazon_scraping.py

import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import time
import re
import random
import json
from urllib.parse import quote_plus

load_dotenv()
USER_AGENT = os.getenv("USER_AGENT")
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")
USE_PROXY = os.getenv("USE_PROXY", "true").lower() == "true"

headers = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

proxies = {}
if USE_PROXY and PROXY_HOST and PROXY_PORT and PROXY_USERNAME and PROXY_PASSWORD:
    proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
    proxies = {'http': proxy_url, 'https': proxy_url}
    print("Proxy ativado para scraping da Amazon.")
else:
    print("Proxy da Amazon desativado.")

# ... (O restante do arquivo amazon_scraping.py permanece o mesmo)
def parse_price_amazon(price_str):
    """
    Converter preço da Amazon para float para cálculos matemáticos
    """
    if not price_str:
        return 0.0
    try:
        # Remover R$ e espaços
        cleaned = str(price_str).replace('R$', '').strip()
        # Extrair apenas números, pontos e vírgulas
        cleaned = re.sub(r'[^\d.,]', '', cleaned)
        # Tratar casos onde há pontos como separadores de milhares e vírgula como decimal
        # Ex: 1.234,56 -> 1234.56
        if ',' in cleaned and '.' in cleaned:
            # Se há tanto ponto quanto vírgula, assumir formato brasileiro (1.234,56)
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            # Se há apenas vírgula, substituir por ponto
            cleaned = cleaned.replace(',', '.')
        # Converter para float
        return float(cleaned) if cleaned else 0.0
    except (ValueError, TypeError):
        return 0.0

def format_amazon_price(symbol, whole, fraction):
    """
    Formatar preço da Amazon corrigindo problemas de dupla vírgula e formatação
    """
    if not whole or str(whole).strip() == '':
        return 'Preço não disponível'
    
    # Limpar e normalizar symbol
    if symbol:
        symbol = symbol.strip()
        if not symbol.startswith('R$'):
            symbol = 'R$'
    else:
        symbol = 'R$'
    
    # Limpar whole (parte inteira)
    whole = str(whole).strip().replace(',', '').replace('.', '')
    if not whole.isdigit():
        # Extrair apenas números
        whole = re.sub(r'\D', '', whole)
    
    if not whole:
        return 'Preço não disponível'
    
    # Processar fraction (centavos)
    if fraction and str(fraction).strip():
        fraction = str(fraction).strip().replace(',', '').replace('.', '')
        # Extrair apenas números dos centavos
        fraction = re.sub(r'\D', '', fraction)

        # Garantir que tenha exatamente 2 dígitos
        if len(fraction) == 1:
            fraction = fraction + '0'  # 5 -> 50
        elif len(fraction) > 2:
            fraction = fraction[:2]  # 500 -> 50
        elif len(fraction) == 0:
            fraction = '00'
    else:
        fraction = '00'
    
    return f"{symbol} {whole},{fraction}"

def sanitize_amazon_price(price_str):
    """
    Sanitizar preços da Amazon que podem ter formatação problemática
    """
    if not price_str or price_str == 'Preço não disponível':
        return price_str

    # Limpar string básica
    price_str = str(price_str).strip()

    # Remover duplas vírgulas e problemas comuns
    price_str = re.sub(r',{2,}', ',', price_str)
    price_str = re.sub(r'\.{2,}', '.', price_str)

    # Padrão principal: R$ 1.234,56 ou R$1234,56
    pattern1 = r'(R\$?\s*)?(\d{1,3}(?:\.\d{3})*),(\d{1,2})'
    match = re.search(pattern1, price_str)
    if match:
        whole = match.group(2).replace('.', '')  # Remove separadores de milhares
        fraction = match.group(3)

        # Garantir que fraction tenha 2 dígitos
        if len(fraction) == 1:
            fraction = fraction + '0'

        return f"R$ {whole},{fraction}"

    # Padrão alternativo: R$ 123.45 (formato americano convertido)
    pattern2 = r'(R\$?\s*)?(\d+)\.(\d{1,2})'
    match = re.search(pattern2, price_str)
    if match:
        whole = match.group(2)
        fraction = match.group(3)

        # Garantir que fraction tenha 2 dígitos
        if len(fraction) == 1:
            fraction = fraction + '0'

        return f"R$ {whole},{fraction}"

    # Fallback: extrair números básicos
    numbers = re.findall(r'\d+', price_str)
    if len(numbers) >= 2:
        whole = numbers[0]
        fraction = numbers[1][:2]  # Máximo 2 dígitos para centavos
        if len(fraction) == 1:
            fraction = fraction + '0'
        return f"R$ {whole},{fraction}"
    elif len(numbers) == 1 and len(numbers[0]) > 2:
        # Assumir que os últimos 2 dígitos são centavos
        num = numbers[0]
        if len(num) > 2:
            whole = num[:-2]
            fraction = num[-2:]
            return f"R$ {whole},{fraction}"
        else:
            return f"R$ {num},00"
    elif len(numbers) == 1:
        return f"R$ {numbers[0]},00"

    return price_str
def extrair_imagem_amazon(produto_elem):
    try:
        img_elem = produto_elem.select_one('img.s-image')
        if img_elem:
            src = img_elem.get('src')
            if src and 'http' in src:
                return re.sub(r'_AC_.*?.jpg', '_AC_SL1500_.jpg', src)
    except Exception:
        pass
    return ""
def extrair_preco_amazon(produto_elem):
    preco_info = {'preco_atual': 'Preço não disponível', 'preco_original': None, 'desconto': None, 'tem_promocao': False}
    try:
        # Estratégia 1: Buscar elementos .a-offscreen (mais confiável)
        preco_atual_selectors = [
            # Preço principal (apex)
            '.a-price.a-text-price.a-size-medium.apexPriceToPay .a-offscreen',
            'span.a-price[data-a-size="xl"] .a-offscreen',
            'span.a-price[data-a-size="l"] .a-offscreen',
            # Preço atual genérico
            '.a-price:not(.a-text-price) .a-offscreen',
            '.a-price-whole',
            # Fallbacks
            'span[data-a-color="price"] .a-offscreen',
            '.a-color-price .a-offscreen'
        ]

        preco_atual_elem = None
        for selector in preco_atual_selectors:
            elementos = produto_elem.select(selector)
            for elem in elementos:
                # Filtrar elementos que estão em seções de produtos relacionados
                parent_text = elem.find_parent(['div', 'span'], class_=lambda x: x and any(
                    keyword in ' '.join(x) for keyword in ['similarity', 'bundle', 'related', 'sponsored']
                )) if elem.find_parent(['div', 'span']) else None

                if not parent_text:
                    texto = elem.get_text().strip()
                    if texto and ('R$' in texto or 'R $' in texto or re.search(r'\d', texto)):
                        preco_info['preco_atual'] = sanitize_amazon_price(texto)
                        preco_atual_elem = elem
                        break

            if preco_atual_elem:
                break

        # Estratégia 2: Se ainda não encontrou, tentar construir a partir de partes
        if not preco_atual_elem or preco_info['preco_atual'] == 'Preço não disponível':
            # Buscar em containers de preço
            price_containers = produto_elem.select('.a-price')
            for container in price_containers:
                # Evitar preços de produtos relacionados
                if container.find_parent(['div'], class_=lambda x: x and any(
                    keyword in ' '.join(x) for keyword in ['similarity', 'bundle', 'related', 'sponsored']
                )):
                    continue

                symbol_elem = container.select_one('.a-price-symbol')
                whole_elem = container.select_one('.a-price-whole')
                fraction_elem = container.select_one('.a-price-fraction')

                if whole_elem:
                    symbol = symbol_elem.get_text().strip() if symbol_elem else 'R$'
                    whole = whole_elem.get_text().strip()
                    fraction = fraction_elem.get_text().strip() if fraction_elem else "00"

                    # Validar que é um número válido
                    whole_clean = re.sub(r'[^\d]', '', whole)
                    if whole_clean and whole_clean.isdigit():
                        preco_info['preco_atual'] = format_amazon_price(symbol, whole, fraction)
                        break
        
        # Estratégia 3: Buscar preço original (riscado/de referência)
        preco_original_selectors = [
            # Preços riscados
            '.a-price.a-text-price .a-offscreen',
            'span.a-price.a-text-price.a-size-base .a-offscreen',
            '.basisPrice .a-offscreen',
            'span[data-a-strike="true"] .a-offscreen',
            '.a-price-was .a-offscreen',
            '.a-text-strike .a-offscreen',
            's .a-offscreen'
        ]

        preco_original_elem = None
        for selector in preco_original_selectors:
            elementos = produto_elem.select(selector)
            for elem in elementos:
                texto = elem.get_text().strip()
                # Garantir que é diferente do preço atual
                if texto and texto != preco_info['preco_atual']:
                    preco_sanitizado = sanitize_amazon_price(texto)
                    if preco_sanitizado and preco_sanitizado != preco_info['preco_atual']:
                        preco_info['preco_original'] = preco_sanitizado
                        preco_info['tem_promocao'] = True
                        preco_original_elem = elem
                        break

            if preco_original_elem:
                break

        # Estratégia 4: Se ainda não encontrou preço original, tentar construir com partes
        if not preco_original_elem or not preco_info['preco_original']:
            # Buscar em containers de preço riscado
            striked_containers = produto_elem.select('.a-price.a-text-price, .basisPrice, s')
            for container in striked_containers:
                symbol_elem = container.select_one('.a-price-symbol')
                whole_elem = container.select_one('.a-price-whole')
                fraction_elem = container.select_one('.a-price-fraction')

                if whole_elem:
                    symbol = symbol_elem.get_text().strip() if symbol_elem else 'R$'
                    whole = whole_elem.get_text().strip()
                    fraction = fraction_elem.get_text().strip() if fraction_elem else "00"

                    # Validar que é um número válido
                    whole_clean = re.sub(r'[^\d]', '', whole)
                    if whole_clean and whole_clean.isdigit():
                        preco_formatado = format_amazon_price(symbol, whole, fraction)
                        # Garantir que é diferente do preço atual
                        if preco_formatado != preco_info['preco_atual']:
                            preco_info['preco_original'] = preco_formatado
                            preco_info['tem_promocao'] = True
                            break
        
        # Estratégia 5: Buscar indicadores de desconto
        discount_selectors = [
            '.savingsPercentage',
            '.a-badge-label',
            'span[aria-label*="%"]',
            '.a-size-mini.a-color-price',
            'span.a-letter-space',
            '.a-color-price.a-size-base',
            '.a-badge-text'
        ]

        for selector in discount_selectors:
            elementos = produto_elem.select(selector)
            for discount_elem in elementos:
                discount_text = discount_elem.get_text().strip()
                # Procurar padrões de desconto
                match = re.search(r'(\d+)%\s*(?:OFF|off|desconto|de\s+desconto)', discount_text, re.IGNORECASE)
                if not match:
                    match = re.search(r'(\d+)%', discount_text)
                if match:
                    desconto_pct = int(match.group(1))
                    # Validar que o desconto faz sentido (entre 1 e 99)
                    if 0 < desconto_pct < 100:
                        preco_info['desconto'] = desconto_pct
                        preco_info['tem_promocao'] = True
                        break

            if preco_info['desconto']:
                break

        # Estratégia 6: Se temos preços mas não desconto, calcular
        if not preco_info['desconto'] and preco_info['preco_original'] and preco_info['preco_atual'] != 'Preço não disponível':
            try:
                atual = parse_price_amazon(preco_info['preco_atual'])
                original = parse_price_amazon(preco_info['preco_original'])
                if original > atual > 0:
                    desconto_pct = int(((original - atual) / original) * 100)
                    if 0 < desconto_pct < 100:
                        preco_info['desconto'] = desconto_pct
                        preco_info['tem_promocao'] = True
            except Exception as calc_error:
                print(f"Erro ao calcular desconto: {calc_error}")

    except Exception as e:
        print(f"DEBUG PRECOS (Busca Amazon): Erro ao extrair preços: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

    return preco_info
def extrair_rating_amazon(produto_elem):
    rating, reviews = "", ""
    try:
        # Seletores atualizados para rating
        rating_selectors = [
            '.a-icon-alt',
            'span[aria-label*="de 5 estrelas"]',
            '.a-icon-star .a-icon-alt',
            '.a-star-medium .a-icon-alt'
        ]

        for selector in rating_selectors:
            rating_elem = produto_elem.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get_text()
                match = re.search(r'(\d[,.]\d)', rating_text)
                if match:
                    rating = match.group(1).replace(',', '.')
                    break

        # Seletores atualizados para reviews
        reviews_selectors = [
            '.a-size-base',
            'a[href*="#customerReviews"]',
            'span[aria-label*="avaliações"]',
            '.a-link-normal'
        ]

        for selector in reviews_selectors:
            reviews_elem = produto_elem.select_one(selector)
            if reviews_elem:
                reviews_text = reviews_elem.get_text().strip()
                # Verificar se contém números que podem ser reviews
                if re.search(r'\d+', reviews_text) and ('(' in reviews_text or 'avaliação' in reviews_text.lower()):
                    reviews = re.sub(r'[^\d.,]', '', reviews_text)
                    break
                elif re.match(r'^\(?\d{1,3}(?:\.\d{3})*\)?$', reviews_text):
                    reviews = reviews_text.strip('()')
                    break
    except Exception:
        pass
    return rating, reviews
def gerar_link_afiliado_amazon(url, affiliate_tag=None):
    amazon_tag = affiliate_tag or os.getenv("AMAZON_ASSOCIATES_TAG", "promobrothers-20")
    if not url or "amzn.to/" in url:
        return url
    if "amazon.com" in url and amazon_tag and amazon_tag != "SEU_TAG_AQUI-20":
        base_url = url.split('?')[0]
        base_url = re.sub(r'/ref=.*', '', base_url)
        return f"{base_url}?tag={amazon_tag}&linkCode=osi"
    return url
def scrape_produto_amazon_especifico(url, afiliado_link=None, max_retries=3, use_api=True):
    """
    Scraping robusto de produto Amazon com retry automático

    Args:
        url: URL do produto
        afiliado_link: Link de afiliado (opcional)
        max_retries: Número máximo de tentativas
        use_api: Se True, usa ScraperAPI; se False, usa requisição direta
    """
    last_error = None
    scraperapi_key = os.getenv("SCRAPERAPI_KEY")

    for tentativa in range(max_retries):
        try:
            if tentativa > 0:
                wait_time = random.uniform(2, 5) * (tentativa + 1)
                print(f"⏳ Aguardando {wait_time:.1f}s antes da tentativa {tentativa + 1}/{max_retries}...")
                time.sleep(wait_time)

            # Decidir se usa ScraperAPI
            usar_api = use_api and scraperapi_key and scraperapi_key != ""

            if usar_api:
                print(f"🔍 Fazendo scraping do produto Amazon via ScraperAPI: {url} (tentativa {tentativa + 1}/{max_retries})")
                api_url = 'http://api.scraperapi.com'
                payload = {
                    'api_key': scraperapi_key,
                    'url': url,
                    'render': 'false'  # Amazon não precisa de JavaScript rendering
                }
                response = requests.get(api_url, params=payload, timeout=60)
            else:
                print(f"🔍 Fazendo scraping do produto Amazon (direto): {url} (tentativa {tentativa + 1}/{max_retries})")
                response = requests.get(url, headers=headers, proxies=proxies, timeout=20)

            # Se recebeu 503/500, tentar novamente
            if response.status_code in [503, 500, 429]:
                print(f"⚠️ Servidor retornou {response.status_code}, tentando novamente...")
                last_error = Exception(f"HTTP {response.status_code}")
                continue

            # Se 404, produto não existe
            if response.status_code == 404:
                print(f"❌ Produto não encontrado (404): {url}")
                return None

            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Verificar se a página tem conteúdo válido
            if not soup or not soup.find():
                print("⚠️ Página vazia ou mal formatada, tentando novamente...")
                last_error = Exception("Página vazia")
                continue

            produto = {'link': url}

            # Extrair nome do produto com fallbacks
            nome_selectors = ['#productTitle', 'h1[data-automation-id="product-title"]', '.product-title']
            for selector in nome_selectors:
                nome_elem = soup.select_one(selector)
                if nome_elem:
                    produto['nome'] = nome_elem.get_text().strip()
                    break
            if 'nome' not in produto:
                produto['nome'] = 'Produto sem título'

            # Extrair imagem com múltiplas estratégias
            img_tag = soup.select_one('#landingImage, #imgTagWrapperId img, #imgBlkFront')
            if img_tag:
                if img_tag.has_attr('data-a-dynamic-image'):
                    try:
                        img_json = json.loads(img_tag['data-a-dynamic-image'])
                        produto['imagem'] = list(img_json.keys())[0]
                    except:
                        produto['imagem'] = img_tag.get('src', '')
                else:
                    produto['imagem'] = img_tag.get('src') or img_tag.get('data-old-hires', '')
            else:
                produto['imagem'] = ''

            # Estratégia 1: Buscar preço atual - containers principais
            preco_atual_selectors = [
                # Containers de preço principal
                '#corePrice_feature_div .a-price:not(.a-text-price) .a-offscreen',
                '#apex_desktop .a-price .a-offscreen',
                '#corePrice_desktop .a-price .a-offscreen',
                '.a-price.apexPriceToPay .a-offscreen',
                'span.a-price[data-a-size="xl"] .a-offscreen',
                'span.a-price[data-a-size="l"] .a-offscreen',
                # Fallbacks genéricos
                '.a-price:not(.a-text-price) .a-offscreen'
            ]

            produto['preco_atual'] = 'Preço não disponível'
            for selector in preco_atual_selectors:
                elementos = soup.select(selector)
                for elem in elementos:
                    # Evitar preços de produtos relacionados/sugeridos
                    parent_section = elem.find_parent(['div'], id=lambda x: x and any(
                        keyword in x for keyword in ['similarities', 'bundle', 'btf', 'anonCarousel']
                    ))
                    if not parent_section:
                        texto = elem.get_text().strip()
                        if texto and ('R$' in texto or re.search(r'\d', texto)):
                            produto['preco_atual'] = sanitize_amazon_price(texto)
                            print(f"✅ Preço atual encontrado: {produto['preco_atual']}")
                            break

                if produto['preco_atual'] != 'Preço não disponível':
                    break

            # Estratégia 2: Se ainda não encontrou, tentar construir com partes
            if produto['preco_atual'] == 'Preço não disponível':
                price_containers = soup.select('#corePrice_feature_div .a-price, #apex_desktop .a-price')
                for container in price_containers:
                    # Verificar se não é preço riscado
                    if 'a-text-price' in container.get('class', []):
                        continue

                    whole_elem = container.select_one('.a-price-whole')
                    fraction_elem = container.select_one('.a-price-fraction')

                    if whole_elem:
                        symbol = container.select_one('.a-price-symbol')
                        symbol_text = symbol.get_text().strip() if symbol else 'R$'
                        whole = whole_elem.get_text().strip()
                        fraction = fraction_elem.get_text().strip() if fraction_elem else "00"

                        # Validar número
                        whole_clean = re.sub(r'[^\d]', '', whole)
                        if whole_clean and whole_clean.isdigit():
                            produto['preco_atual'] = format_amazon_price(symbol_text, whole, fraction)
                            print(f"✅ Preço atual construído: {produto['preco_atual']}")
                            break

            # Estratégia 3: Buscar preço original (riscado)
            preco_original_selectors = [
                '.basisPrice .a-offscreen',
                '.a-price.a-text-price .a-offscreen',
                'span.a-price.a-text-price .a-offscreen',
                'span[data-a-strike="true"] .a-offscreen',
                '.a-price-was .a-offscreen',
                '#corePrice_desktop .a-text-price .a-offscreen',
                's .a-offscreen'
            ]

            produto['preco_original'] = None
            for selector in preco_original_selectors:
                elementos = soup.select(selector)
                for elem in elementos:
                    texto = elem.get_text().strip()
                    if texto and texto != produto['preco_atual']:
                        preco_sanitizado = sanitize_amazon_price(texto)
                        if preco_sanitizado and preco_sanitizado != produto['preco_atual']:
                            produto['preco_original'] = preco_sanitizado
                            print(f"✅ Preço original encontrado: {produto['preco_original']}")
                            break

                if produto['preco_original']:
                    break

            # Estratégia 4: Se ainda não encontrou preço original, tentar construir com partes
            if not produto['preco_original']:
                striked_containers = soup.select('.basisPrice, .a-price.a-text-price, s')
                for container in striked_containers:
                    symbol_elem = container.select_one('.a-price-symbol')
                    whole_elem = container.select_one('.a-price-whole')
                    fraction_elem = container.select_one('.a-price-fraction')

                    if whole_elem:
                        symbol = symbol_elem.get_text().strip() if symbol_elem else 'R$'
                        whole = whole_elem.get_text().strip()
                        fraction = fraction_elem.get_text().strip() if fraction_elem else "00"

                        whole_clean = re.sub(r'[^\d]', '', whole)
                        if whole_clean and whole_clean.isdigit():
                            preco_formatado = format_amazon_price(symbol, whole, fraction)
                            if preco_formatado != produto['preco_atual']:
                                produto['preco_original'] = preco_formatado
                                print(f"✅ Preço original construído: {produto['preco_original']}")
                                break

            # Estratégia 5: Buscar desconto
            desconto = None
            discount_selectors = [
                '.savingsPercentage',
                '.savingPriceOverride',
                '.a-badge-label',
                'span[aria-label*="%"]',
                '.a-size-large.a-color-price',
                '#apex_desktop .savingsPercentage',
                '.a-badge-text'
            ]

            for selector in discount_selectors:
                elementos = soup.select(selector)
                for discount_elem in elementos:
                    discount_text = discount_elem.get_text().strip()
                    match = re.search(r'(\d+)%\s*(?:OFF|off|desconto|de\s+desconto)', discount_text, re.IGNORECASE)
                    if not match:
                        match = re.search(r'(\d+)%', discount_text)
                    if match:
                        desconto_pct = int(match.group(1))
                        if 0 < desconto_pct < 100:
                            desconto = desconto_pct
                            print(f"✅ Desconto encontrado: {desconto}%")
                            break

                if desconto:
                    break

            # Estratégia 6: Se não encontrou desconto direto mas tem preços, calcular
            if not desconto and produto['preco_original'] and produto['preco_atual'] != 'Preço não disponível':
                try:
                    atual = parse_price_amazon(produto['preco_atual'])
                    original = parse_price_amazon(produto['preco_original'])
                    if original > atual > 0:
                        desconto_pct = int(((original - atual) / original) * 100)
                        if 0 < desconto_pct < 100:
                            desconto = desconto_pct
                            print(f"✅ Desconto calculado: {desconto}%")
                except Exception as calc_error:
                    print(f"Erro ao calcular desconto: {calc_error}")

            produto['desconto'] = desconto
            produto['tem_promocao'] = bool(produto['preco_original'] and desconto)
            produto['rating'], produto['reviews'] = extrair_rating_amazon(soup)
            produto['fonte'] = 'Amazon'
            produto['comissao_pct'] = "8.0"
            produto['link_afiliado'] = afiliado_link or gerar_link_afiliado_amazon(url)
            print(f"✅ Produto Amazon extraído com sucesso: {produto['nome'][:50]}...")
            print(f"   Preço: {produto['preco_atual']} | Original: {produto['preco_original']} | Desconto: {desconto}%")
            return produto

        except requests.RequestException as req_error:
            print(f"⚠️ Erro de requisição (tentativa {tentativa + 1}/{max_retries}): {req_error}")
            last_error = req_error
            continue

        except Exception as parse_error:
            print(f"⚠️ Erro ao processar HTML (tentativa {tentativa + 1}/{max_retries}): {parse_error}")
            last_error = parse_error
            continue

    # Se chegou aqui, todas as tentativas falharam
    print(f"❌ Falha após {max_retries} tentativas")
    if last_error:
        import traceback
        print(f"Último erro: {last_error}")
        print(f"Traceback: {traceback.format_exc()}")
    return None
def scrape_amazon(produto, max_pages=2, categoria="", max_retries=2, use_api=True):
    """
    Scraping robusto de busca Amazon com retry automático

    Args:
        produto: Termo de busca
        max_pages: Número máximo de páginas
        categoria: Categoria (não usado)
        max_retries: Número máximo de tentativas por página
        use_api: Se True, usa ScraperAPI; se False, usa requisição direta
    """
    produtos = []
    produto_formatado = quote_plus(produto)
    scraperapi_key = os.getenv("SCRAPERAPI_KEY")

    for page in range(1, max_pages + 1):
        page_success = False

        for tentativa in range(max_retries):
            try:
                if tentativa > 0:
                    wait_time = random.uniform(3, 6)
                    print(f"⏳ Aguardando {wait_time:.1f}s antes de tentar novamente...")
                    time.sleep(wait_time)

                url = f'https://www.amazon.com.br/s?k={produto_formatado}&page={page}'

                # Decidir se usa ScraperAPI
                usar_api = use_api and scraperapi_key and scraperapi_key != ""

                if usar_api:
                    print(f"🔍 Fazendo scraping da página {page} via ScraperAPI: {url} (tentativa {tentativa + 1}/{max_retries})")
                    api_url = 'http://api.scraperapi.com'
                    payload = {
                        'api_key': scraperapi_key,
                        'url': url,
                        'render': 'false'
                    }
                    response = requests.get(api_url, params=payload, timeout=60)
                else:
                    print(f"🔍 Fazendo scraping da página {page} (direto): {url} (tentativa {tentativa + 1}/{max_retries})")
                    time.sleep(random.uniform(1.5, 3.5))
                    response = requests.get(url, headers=headers, proxies=proxies, timeout=20)

                # Tratar erros específicos
                if response.status_code in [503, 500, 429]:
                    print(f"⚠️ Servidor retornou {response.status_code}, tentando novamente...")
                    continue

                if response.status_code != 200:
                    print(f"⚠️ Status code: {response.status_code}")
                    if tentativa < max_retries - 1:
                        continue
                    else:
                        print(f"❌ Parando a busca na Amazon após {max_retries} tentativas.")
                        return produtos

                soup = BeautifulSoup(response.content, 'html.parser')

                # Verificar se há conteúdo válido
                if not soup or not soup.find():
                    print("⚠️ Página vazia, tentando novamente...")
                    continue

                produtos_encontrados = soup.select('[data-component-type="s-search-result"]')
                if not produtos_encontrados:
                    print("⚠️ Nenhum produto encontrado nesta página da Amazon.")
                    if tentativa < max_retries - 1:
                        continue
                    else:
                        break

                # Processar produtos encontrados
                print(f"✅ Encontrados {len(produtos_encontrados)} produtos na página {page}")
                for item in produtos_encontrados:
                    try:
                        nome_elem = item.select_one('h2 .a-text-normal')
                        if not nome_elem:
                            continue
                        nome = nome_elem.get_text().strip()
                        link_elem = item.select_one('h2 a')
                        link = f"https://www.amazon.com.br{link_elem['href']}" if link_elem else ""

                        preco_info = extrair_preco_amazon(item)
                        imagem = extrair_imagem_amazon(item)
                        rating, reviews = extrair_rating_amazon(item)

                        produto_dict = {
                            'nome': nome, 'link': link, 'link_afiliado': gerar_link_afiliado_amazon(link),
                            'imagem': imagem, 'comissao_pct': "8.0", 'fonte': 'Amazon',
                            'rating': rating, 'reviews': reviews, **preco_info
                        }
                        produtos.append(produto_dict)
                        print(f"✅ Produto Amazon adicionado: {nome[:50]}... | Preço: {preco_info['preco_atual']}")

                    except Exception as e:
                        print(f"⚠️ Erro ao processar item da Amazon: {e}")
                        continue

                page_success = True
                break  # Sair do loop de retry se teve sucesso

            except requests.RequestException as req_error:
                print(f"⚠️ Erro de requisição (tentativa {tentativa + 1}/{max_retries}): {req_error}")
                if tentativa == max_retries - 1:
                    print(f"❌ Falha na página {page} após {max_retries} tentativas")
                    return produtos
                continue

            except Exception as parse_error:
                print(f"⚠️ Erro ao processar página (tentativa {tentativa + 1}/{max_retries}): {parse_error}")
                if tentativa == max_retries - 1:
                    print(f"❌ Falha na página {page} após {max_retries} tentativas")
                continue

        if not page_success:
            print(f"⚠️ Não foi possível carregar a página {page}, continuando para próxima...")

    print(f"✅ Scraping da Amazon concluído. Total: {len(produtos)} produtos.")
    return produtos