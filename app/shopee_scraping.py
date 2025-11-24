# /app/shopee_scraping.py

import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import time
import re
import json

load_dotenv()
USER_AGENT = os.getenv("USER_AGENT")

# --- NOVIDADE: Adicionando configuração de Proxy ---
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")
USE_PROXY = os.getenv("USE_PROXY", "true").lower() == "true"

headers = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://shopee.com.br/'
}

proxies = {}
if USE_PROXY and PROXY_HOST and PROXY_PORT and PROXY_USERNAME and PROXY_PASSWORD:
    proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
    proxies = {'http': proxy_url, 'https': proxy_url}
    print("Proxy ativado para scraping da Shopee.")
else:
    print("Proxy da Shopee desativado.")
# --- FIM DA NOVIDADE ---


def parse_price_shopee(price_str):
    """Converte uma string de preço para float."""
    if not price_str:
        return 0.0
    try:
        return float(re.sub(r'[^\d]', '', str(price_str))) / 100
    except (ValueError, TypeError):
        return 0.0

def scrape_produto_shopee_especifico(url):
    """Realiza o scraping de uma página de produto específica da Shopee."""
    try:
        # Headers mais completos para evitar bloqueios
        shopee_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

        # Usar proxies apenas se configurados
        use_proxies = proxies if USE_PROXY and proxies else {}

        r = requests.get(url, headers=shopee_headers, proxies=use_proxies, timeout=30)
        r.raise_for_status()

        site = BeautifulSoup(r.content, 'html.parser')
        produto_info = {'link': url}

        # Tentativa 1: JSON-LD
        script_data = site.find('script', type='application/ld+json')
        if script_data:
            try:
                data = json.loads(script_data.string)
                produto_info['titulo'] = data.get('name', 'Título não encontrado')
                produto_info['imagem'] = data.get('image', '')

                offers = data.get('offers', [{}])
                if isinstance(offers, list) and offers:
                    offer = offers[0]
                    price = offer.get('price')
                    if price:
                        produto_info['preco_atual'] = f"R$ {float(price):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    else:
                        produto_info['preco_atual'] = 'Preço não disponível'
                else:
                    produto_info['preco_atual'] = 'Preço não disponível'
            except (json.JSONDecodeError, ValueError, TypeError):
                script_data = None

        # Tentativa 2: Extrair de scripts JavaScript
        if not script_data:
            scripts = site.find_all('script')
            for script in scripts:
                if script.string and ('window.__INITIAL_STATE__' in script.string or 'window.__DATA__' in script.string):
                    try:
                        # Procurar por dados do produto no JavaScript
                        script_content = script.string

                        # Tentar extrair título
                        title_match = re.search(r'"name"\s*:\s*"([^"]+)"', script_content)
                        if title_match and not produto_info.get('titulo'):
                            produto_info['titulo'] = title_match.group(1)

                        # Tentar extrair preço
                        price_match = re.search(r'"price"\s*:\s*(\d+)', script_content)
                        if price_match and not produto_info.get('preco_atual'):
                            price_value = int(price_match.group(1)) / 100000  # Shopee usa preços em unidades pequenas
                            produto_info['preco_atual'] = f"R$ {price_value:.2f}".replace(".", ",")

                        # Tentar extrair imagem
                        img_match = re.search(r'"image"\s*:\s*"([^"]+)"', script_content)
                        if img_match and not produto_info.get('imagem'):
                            img_url = img_match.group(1)
                            if img_url.startswith('//'):
                                img_url = 'https:' + img_url
                            elif not img_url.startswith('http'):
                                img_url = f'https://cf.shopee.com.br/file/{img_url}'
                            produto_info['imagem'] = img_url
                    except Exception:
                        continue

        # Tentativa 3: Seletores CSS tradicionais (fallback)
        if not produto_info.get('titulo'):
            for selector in ['._44qnta', 'h1', '.product-briefing h1', '[data-testid="pdp-product-title"]']:
                titulo_elem = site.select_one(selector)
                if titulo_elem:
                    produto_info['titulo'] = titulo_elem.get_text(strip=True)
                    break
            else:
                produto_info['titulo'] = 'Título não encontrado'

        if not produto_info.get('preco_atual'):
            for selector in ['._3_Fivj', '._2_BY_8', '.product-price', '[data-testid="price"]']:
                preco_elem = site.select_one(selector)
                if preco_elem:
                    preco_text = preco_elem.get_text(strip=True)
                    if preco_text and 'R$' in preco_text:
                        produto_info['preco_atual'] = preco_text
                        break
            else:
                produto_info['preco_atual'] = 'Preço não disponível'

        if not produto_info.get('imagem'):
            for selector in ['._39-Tsj ._12_1rN', '.product-image img', 'img[data-testid="pdp-main-image"]']:
                img_elem = site.select_one(selector)
                if img_elem:
                    src = img_elem.get('src') or img_elem.get('data-src')
                    if src:
                        produto_info['imagem'] = src
                        break
            else:
                produto_info['imagem'] = ''

        # Preço original e desconto
        preco_original_elem = site.select_one('._2_BY_8, .product-price-original')
        produto_info['preco_original'] = f"R$ {preco_original_elem.get_text(strip=True)}" if preco_original_elem else None

        desconto_elem = site.select_one('._2-m6e5, .discount-label')
        produto_info['desconto'] = None
        if desconto_elem:
            match = re.search(r'(\d+)%', desconto_elem.get_text(strip=True))
            if match:
                produto_info['desconto'] = int(match.group(1))

        # Calcular desconto se não encontrado
        if not produto_info.get('desconto') and produto_info.get('preco_original') and produto_info.get('preco_atual') != 'Preço não disponível':
            try:
                preco_atual_float = parse_price_shopee(produto_info['preco_atual'])
                preco_original_float = parse_price_shopee(produto_info['preco_original'])
                if preco_original_float > preco_atual_float > 0:
                    produto_info['desconto'] = int(((preco_original_float - preco_atual_float) / preco_original_float) * 100)
            except:
                pass

        produto_info['tem_promocao'] = bool(produto_info.get('preco_original') and produto_info.get('desconto'))

        # Loja
        loja_elem = site.select_one('._3_0f-8, .shop-name')
        produto_info['loja'] = loja_elem.get_text(strip=True) if loja_elem else ''

        return produto_info

    except requests.RequestException as e:
        print(f"Erro de requisição ao buscar produto Shopee: {e}")
        return None
    except Exception as e:
        print(f"Erro ao processar página de produto Shopee: {e}")
        return None

def scrape_shopee(produto, max_pages=1):
    """Realiza busca de produtos na Shopee."""
    print(f"Busca na Shopee por '{produto}' - Aviso: A Shopee requer URLs específicas de produtos para melhor funcionamento")

    # Como a Shopee bloqueia buscas automatizadas, vamos retornar uma mensagem explicativa
    resultados = [{
        'titulo': f'Busca por "{produto}" na Shopee',
        'preco_atual': 'Preço não disponível',
        'preco_original': None,
        'desconto': None,
        'tem_promocao': False,
        'imagem': '',
        'link': f'https://shopee.com.br/search?keyword={produto.replace(" ", "%20")}',
        'loja': 'Shopee',
        'nota': 'Para melhor funcionamento, cole uma URL específica de produto da Shopee'
    }]

    return resultados