# /mercado_livre_scraper/app/scraping.py

import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import time
import re

load_dotenv()
USER_AGENT = os.getenv("USER_AGENT")
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")

# =========================================================================
# ⭐ NOVO: COOKIES DE LOGIN DO MERCADO LIVRE
# Estes cookies garantem que as requisições sejam feitas na sua sessão,
# o que é crucial para links de afiliado, taxas e visualização correta.
# [cite_start]Os dados foram extraídos das suas fontes[cite: 4, 5, 6].
# =========================================================================
ML_COOKIES = (
    "_csrf=bKhKU-g6VetNitGbSos7ud5y; "
    "ssid=ghy-092623-TUq9JJcPx2qXkkMm4UxZVdqXrGEJz7-__-404150719-__-1853637093730--RRR_0-RRR_0; "
    "orguserid=HTddTt09dh04; "
    "orguseridp=404150719; "
    "nsa_rotok=eyJhbGciOiJSUzI1NiIsImtpZCI6IjMiLCJ0eXAiOiJKV1QifQ.eyJpZGVudGlmaWVyIjoiMzRjOWFmYTctNWExMS00M2QyLTk4MWItZGUxYjgyY2QxMmJhIiwicm90YXRpb25fZGF0ZSI6MTc2MjIxMjMyMSwiZXhwIjoxNzY0ODAzNzIxLCJqdGkiOiI5ZGU0ZmVlNC1lYzE2LTQ0ZTUtYjE2Yi1kMDg3YzAwNDJhMGIiLCJpYXQiOjE3NjIyMTE3MjEsInN1YiI6IjM0YzlhZmE3LTVhMTEtNDNkMi05ODFiLWRlMWI4MmNkMTJiYSJ9.cNvq922U-t2a7Ife9Viw9sNWgU3sOpltm3MSvrX0A75HHHN7E51-I9r_ABduvyk0X2l1U7lvT2cDPamxL5K5F9hEEnqn5hg6NhUMc_oi9o5TgeWbuFMvjUf8W4D81FHjqlCZ5h8QijgHaULIcOEH7gdOHMY7fYrxHvvucWiJmIsL-EKTpfaIWheow6y_1hJpOIFSqKyxeFs5rUSkJsyKnsHzI1b8jpfU1rME1R-IGSZZeW9FiA57FxCg7OOEo0KUG-T7t0sE1OQ9u7luNy3uIN6_vDEs6hGmByni1qn2roeUsuOrSUMu6zrIk51INI0uwKMgPFI8O7zZCaToqV2Gjg; "
    "cookiesPreferencesLogged=%7B%22userId%22%3A404150719%2C%22categories%22%3A%7B%22advertising%22%3Atrue%2C%22functionality%22%3Atrue%2C%22performance%22%3Atrue%2C%22traceability%22%3Atrue%7D%7D; "
    "hide-cookie-banner=404150719-COOKIE_PREFERENCES_ALREADY_SET; "
    "ml_cart-quantity=1; "
    "LAST_SEARCH=cv700m"
)

headers = {
    'User-Agent': USER_AGENT,
    'Cookie': ML_COOKIES # ⭐ Adiciona o header de Cookie
}

proxies = {}
if PROXY_HOST and PROXY_PORT and PROXY_USERNAME and PROXY_PASSWORD:
    proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
    proxies = {'http': proxy_url, 'https': proxy_url}

def parse_price(price_str):
    """Converte uma string de preço (ex: 'R$ 1.234,56') para um float."""
    if not price_str:
        return 0.0
    try:
        cleaned_price = re.sub(r'[^\d,.]', '', str(price_str))
        if ',' in cleaned_price and '.' in cleaned_price:
             cleaned_price = cleaned_price.replace('.', '').replace(',', '.')
        else:
             cleaned_price = cleaned_price.replace(',', '.')
        return float(cleaned_price)
    except (ValueError, TypeError):
        return 0.0

def scrape_produto_especifico(url):
    """Realiza o scraping de uma página de produto específica do Mercado Livre com lógica aprimorada."""
    try:
        # headers com cookie são usados aqui
        r = requests.get(url, headers=headers, proxies=proxies, timeout=20)
        r.raise_for_status()

        site = BeautifulSoup(r.content, 'html.parser')

        # Detectar se redirecionou para página social e extrair link real do produto
        if '/social/' in r.url and '/social/' not in url:
            print(f"Link redirecionou para página social. Buscando link real do produto...")

            # Tentar encontrar link do produto na página social
            all_links = site.find_all('a', href=True)
            product_link = None

            # Buscar por links que contenham /p/ ou /MLB- (links de produto)
            for link in all_links:
                href = link.get('href', '')
                if ('/p/MLB' in href or '/MLB-' in href) and 'mercadolivre.com.br' in href:
                    # Limpar parâmetros desnecessários
                    product_link = href.split('#')[0].split('?')[0]
                    if product_link.startswith('http'):
                        print(f"Link real do produto encontrado: {product_link}")
                        # Fazer nova requisição para o produto real
                        r = requests.get(product_link, headers=headers, proxies=proxies, timeout=20)
                        r.raise_for_status()
                        site = BeautifulSoup(r.content, 'html.parser')
                        url = product_link
                        break

        produto_info = {'link': url}

        # --- Título com fallbacks (incluindo OpenGraph) ---
        titulo_selectors = ['h1.ui-pdp-title', 'h2.ui-pdp-title', 'h1']
        titulo_elem = None
        for selector in titulo_selectors:
            titulo_elem = site.select_one(selector)
            if titulo_elem:
                break

        if titulo_elem:
            produto_info['titulo'] = titulo_elem.get_text(strip=True)
        else:
            # Fallback para meta tags OpenGraph
            og_title = site.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                produto_info['titulo'] = og_title.get('content').strip()
            else:
                meta_title = site.find('meta', attrs={'name': 'title'})
                if meta_title and meta_title.get('content'):
                    produto_info['titulo'] = meta_title.get('content').strip()
                else:
                    produto_info['titulo'] = 'Título não encontrado'

        # --- IMAGEM (LÓGICA CORRIGIDA COM FALLBACKS INCLUINDO OPENGRAPH) ---
        produto_info['imagem'] = ''
        image_selectors = [
            '.ui-pdp-gallery__figure img',
            '[data-testid="gallery-main-picture"] img',
            '.ui-pdp-image.ui-pdp-gallery__figure__image',
            'img[data-zoom]',
            'figure img',
            '.ui-pdp-gallery img'
        ]
        for selector in image_selectors:
            img_elem = site.select_one(selector)
            if img_elem:
                src = img_elem.get('data-zoom') or img_elem.get('src') or ''
                if src and 'http' in src:
                    src = src.replace('-I.jpg', '-O.jpg').replace('-I.webp', '-O.webp')
                    produto_info['imagem'] = src
                    break

        # Fallback para OpenGraph image
        if not produto_info['imagem']:
            og_image = site.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                src = og_image.get('content')
                if src and 'http' in src:
                    src = src.replace('-I.jpg', '-O.jpg').replace('-I.webp', '-O.webp')
                    produto_info['imagem'] = src

        # --- Lógica de Preço Aprimorada com mais fallbacks ---
        preco_atual_str = "Preço não disponível"
        preco_original_str = None
        desconto_val = None

        # Tentar múltiplas meta tags de preço
        meta_price_elem = site.find('meta', itemprop='price')
        if not meta_price_elem:
            meta_price_elem = site.find('meta', property='product:price:amount')

        if meta_price_elem and meta_price_elem.has_attr('content'):
            try:
                price_float = float(meta_price_elem['content'])
                preco_atual_str = f"R$ {price_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except:
                pass
        
        if preco_atual_str == "Preço não disponível":
            price_selectors = [
                '.ui-pdp-price__main-container .andes-money-amount__fraction',
                '.price-tag-amount .andes-money-amount__fraction',
                '.ui-pdp-price__fraction',
                '.andes-money-amount--cents-superscript .andes-money-amount__fraction',
                'span.andes-money-amount__fraction',
                '.poly-price__current .andes-money-amount__fraction'
            ]
            for selector in price_selectors:
                price_elem = site.select_one(selector)
                if price_elem:
                    # Buscar centavos em contextos relevantes
                    centavos_elem = price_elem.find_next_sibling(class_='andes-money-amount__cents')
                    if not centavos_elem:
                        centavos_elem = site.select_one('.andes-money-amount__cents')
                    centavos = f",{centavos_elem.get_text(strip=True)}" if centavos_elem and centavos_elem.get_text(strip=True) else ",00"
                    preco_atual_str = f"R$ {price_elem.get_text(strip=True)}{centavos}"
                    break

        original_price_selectors = [
            's .andes-money-amount__fraction',
            '.ui-pdp-price__original-value .andes-money-amount__fraction'
        ]
        for selector in original_price_selectors:
            original_price_elem = site.select_one(selector)
            if original_price_elem:
                preco_original_valor = original_price_elem.get_text(strip=True)

                # Buscar centavos do preço original na página específica
                centavos_original_elem = site.select_one('s .andes-money-amount__cents, .ui-pdp-price__original-value .andes-money-amount__cents')
                centavos_original = f",{centavos_original_elem.get_text(strip=True)}" if centavos_original_elem and centavos_original_elem.get_text(strip=True) else ",00"

                preco_original_str = f"R$ {preco_original_valor}{centavos_original}"
                break
        
        discount_selectors = [
            '.ui-pdp-price__discount',
            '.ui-pdp-media__discount'
        ]
        for selector in discount_selectors:
            discount_elem = site.select_one(selector)
            if discount_elem:
                match = re.search(r'(\d+)%', discount_elem.get_text(strip=True))
                if match:
                    desconto_val = int(match.group(1))
                    break

        if not desconto_val and preco_original_str and preco_atual_str != "Preço não disponível":
            try:
                preco_atual_float = parse_price(preco_atual_str)
                preco_original_float = parse_price(preco_original_str)
                if preco_original_float > preco_atual_float > 0:
                    desconto_val = int(((preco_original_float - preco_atual_float) / preco_original_float) * 100)
            except:
                pass

        produto_info['preco_atual'] = preco_atual_str
        produto_info['preco_original'] = preco_original_str
        produto_info['desconto'] = desconto_val
        produto_info['tem_promocao'] = bool(preco_original_str and desconto_val)

        # --- Outros Detalhes ---
        condicao_elem = site.select_one('.ui-pdp-header__subtitle .ui-pdp-subtitle')
        produto_info['condicao'] = condicao_elem.get_text(strip=True) if condicao_elem else ''

        vendedor_elem = site.select_one('.ui-pdp-seller__header__title')
        produto_info['vendedor'] = vendedor_elem.get_text(strip=True) if vendedor_elem else ''
        
        # --- Adicionando o nome da loja/vendedor ---
        loja_elem = site.select_one('.ui-pdp-seller__link-trigger') 
        if loja_elem:
            produto_info['loja'] = loja_elem.get_text(strip=True)
        else:
            produto_info['loja'] = produto_info.get('vendedor', '') # Fallback para o nome do vendedor

        desc_elem = site.select_one('.ui-pdp-description__content p')
        produto_info['descricao'] = desc_elem.get_text(strip=True) if desc_elem else ''

        produto_info.update({'disponivel': True, 'cupons': []})

        return produto_info

    except requests.RequestException as e:
        print(f"Erro de requisição ao buscar produto específico: {e}")
        return None
    except Exception as e:
        print(f"Erro ao processar página de produto específico: {e}")
        return None


def extrair_imagem_produto(produto_elem):
    try:
        img_selectors = [
            'img.poly-component__picture',
            'img.ui-search-result-image__element',
            'img[data-src]',
            'img.ui-search-item__image',
            '.ui-search-result-image__element',
            'img'
        ]
        for selector in img_selectors:
            img_elem = produto_elem.select_one(selector)
            if img_elem:
                src = img_elem.get('data-src') or img_elem.get('src')
                if src and 'http' in src:
                    # Remove parâmetros de redimensionamento para obter imagem de melhor qualidade
                    src = src.split('?')[0]
                    return src
    except Exception:
        pass
    return ""

def extrair_precos(produto_elem):
    precos_info = {'preco_atual': 'Preço não disponível', 'preco_original': None, 'desconto': None, 'tem_promocao': False}
    try:
        # Múltiplos seletores para preço atual
        preco_atual_selectors = [
            '.andes-money-amount__fraction',
            '.ui-search-price__part .andes-money-amount__fraction',
            '.price-tag-amount .andes-money-amount__fraction',
            '.price-tag .andes-money-amount__fraction'
        ]
        
        preco_atual_elem = None
        for selector in preco_atual_selectors:
            preco_atual_elem = produto_elem.select_one(selector)
            if preco_atual_elem:
                break
        
        if preco_atual_elem:
            preco_atual_str = preco_atual_elem.get_text().strip()
            
            # Buscar centavos em múltiplos possíveis locais
            centavos_selectors = [
                '.andes-money-amount__cents',
                '.price-tag-amount .andes-money-amount__cents',
                '.ui-search-price__part .andes-money-amount__cents'
            ]
            
            centavos_elem = None
            for selector in centavos_selectors:
                centavos_elem = produto_elem.select_one(selector)
                if centavos_elem:
                    break
            
            centavos_str = f",{centavos_elem.get_text().strip()}" if centavos_elem and centavos_elem.get_text().strip() else ",00"
            precos_info['preco_atual'] = f"R$ {preco_atual_str}{centavos_str}"
        
        # Múltiplos seletores para preço original (riscado)
        preco_original_selectors = [
            '.ui-search-price__original-value .andes-money-amount__fraction',
            '.ui-search-price__second-line .andes-money-amount__fraction',
            '.price-tag-original .andes-money-amount__fraction',
            'span.andes-money-amount--previous .andes-money-amount__fraction',
            '.ui-search-item__price-second-line .andes-money-amount__fraction'
        ]

        preco_original_elem = None
        for selector in preco_original_selectors:
            preco_original_elem = produto_elem.select_one(selector)
            if preco_original_elem:
                break

        if preco_original_elem:
            # Buscar centavos do preço original
            preco_original_str = preco_original_elem.get_text().strip()

            # Buscar centavos em seletores específicos para o preço original
            centavos_originais_selectors = [
                '.ui-search-price__original-value .andes-money-amount__cents',
                '.ui-search-price__second-line .andes-money-amount__cents',
                '.price-tag-original .andes-money-amount__cents',
                'span.andes-money-amount--previous .andes-money-amount__cents',
                '.ui-search-item__price-second-line .andes-money-amount__cents'
            ]

            centavos_original_elem = None
            for selector in centavos_originais_selectors:
                centavos_original_elem = produto_elem.select_one(selector)
                if centavos_original_elem:
                    break

            centavos_original_str = f",{centavos_original_elem.get_text().strip()}" if centavos_original_elem and centavos_original_elem.get_text().strip() else ",00"
            precos_info['preco_original'] = f"R$ {preco_original_str}{centavos_original_str}"
            precos_info['tem_promocao'] = True
        
        # Múltiplos seletores para desconto
        desconto_selectors = [
            '.ui-search-price__discount',
            '.ui-search-item__group__element--tag',
            '.ui-search-item__tag',
            '.price-tag-discount',
            'span[class*="discount"]',
            'span[class*="off"]'
        ]
        
        desconto_elem = None
        for selector in desconto_selectors:
            desconto_elem = produto_elem.select_one(selector)
            if desconto_elem:
                desconto_text = desconto_elem.get_text().strip()
                # Procurar por padrões de desconto
                match = re.search(r'(\d+)%?\s*(?:OFF|off|OFF!)', desconto_text, re.IGNORECASE)
                if not match:
                    match = re.search(r'(\d+)%', desconto_text)
                if match:
                    precos_info['desconto'] = int(match.group(1))
                    precos_info['tem_promocao'] = True
                    break
        
        # Se temos preço atual e original mas não desconto, calcular
        if precos_info['preco_atual'] != 'Preço não disponível' and precos_info['preco_original'] and not precos_info['desconto']:
            try:
                atual = parse_price(precos_info['preco_atual'])
                original = parse_price(precos_info['preco_original'])
                if original > atual > 0:
                    desconto_calculado = int(((original - atual) / original) * 100)
                    if desconto_calculado > 0:
                        precos_info['desconto'] = desconto_calculado
                        precos_info['tem_promocao'] = True
            except:
                pass
                
    except Exception as e:
        print(f"DEBUG PRECOS (Busca): Erro ao extrair preços: {e}")
    
    return precos_info

def scrape_mercadolivre(produto, max_pages=3):
    produto_formatado = produto.replace(' ', '-')
    resultados = []
    for page in range(1, max_pages + 1):
        try:
            url_final = f'https://lista.mercadolivre.com.br/{produto_formatado}_Desde_{(page - 1) * 50 + 1}' if page > 1 else f'https://lista.mercadolivre.com.br/{produto_formatado}'
            # headers com cookie são usados aqui
            r = requests.get(url_final, headers=headers, proxies=proxies, timeout=20)
            if r.status_code != 200: break
            site = BeautifulSoup(r.content, 'html.parser')
            produtos_encontrados = site.select('li.ui-search-layout__item')
            if not produtos_encontrados: break
            for produto_elem in produtos_encontrados:
                try:
                    # Seletores atualizados para título
                    titulo_selectors = ['a.poly-component__title', 'h3.poly-component__title-wrapper', 'h2.ui-search-item__title']
                    titulo_elem = None
                    for ts in titulo_selectors:
                        titulo_elem = produto_elem.select_one(ts)
                        if titulo_elem:
                            break

                    # Seletores atualizados para link
                    link_selectors = ['a.poly-component__title', 'a.ui-search-link']
                    link_elem = None
                    for ls in link_selectors:
                        link_elem = produto_elem.select_one(ls)
                        if link_elem:
                            break

                    if not titulo_elem or not link_elem:
                        continue
                    titulo = titulo_elem.get_text().strip()
                    link = link_elem.get('href')
                    precos_info = extrair_precos(produto_elem)
                    imagem_url = extrair_imagem_produto(produto_elem)
                    # A busca não mostra o nome da loja, então deixamos em branco
                    loja = '' 
                    if titulo and link:
                        resultados.append({'titulo': titulo, **precos_info, 'imagem': imagem_url, 'link': link, 'loja': loja})
                except Exception: continue
            time.sleep(2)
        except Exception as e:
            print(f"Erro ao processar página de busca do Mercado Livre: {e}")
            break
    return resultados

def busca_alternativa(produto):
    return []