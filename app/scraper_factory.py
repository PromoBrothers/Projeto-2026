import logging
import time
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from .config import ScrapingConfig
from .anti_bot import AntiBotManager
from .selectors import AdaptiveSelector
from .validators import product_validator
from .cache_manager import cached_scraper
from . import amazon_scraping

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, platform: str):
        self.platform = platform
        self.config = ScrapingConfig.get_platform_config(platform)
        self.anti_bot = AntiBotManager()
        self.selector = AdaptiveSelector(platform)

    @abstractmethod
    def scrape_product(self, url: str, affiliate_link: str = "") -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def scrape_search(self, query: str, max_pages: int = 2) -> List[Dict[str, Any]]:
        pass

    def _validate_and_sanitize(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        return product_validator.validate_product(product_data)

class MercadoLivreScraper(BaseScraper):
    def __init__(self):
        super().__init__('mercadolivre')

    def _extract_real_affiliate_link(self, affiliate_url: str) -> tuple[str, str]:
        """
        Extrai o link real do produto seguindo o link de afiliado
        Retorna (product_url, real_affiliate_link)
        """
        try:
            logger.info(f"🔗 Extraindo link real de afiliado: {affiliate_url[:80]}...")

            import requests
            from urllib.parse import urlparse, parse_qs, unquote

            session = requests.Session()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            # Seguir redirects e capturar URLs intermediárias
            response = session.get(affiliate_url, headers=headers, allow_redirects=True, timeout=30)
            final_url = response.url

            logger.info(f"📍 URL final após redirects: {final_url[:80]}...")

            # Verificar se chegou em uma página de produto
            if '/p/MLB' in final_url or re.search(r'/MLB\d+', final_url):
                # Extrair ID do produto
                product_match = re.search(r'(MLB\d+)', final_url)
                if product_match:
                    product_id = product_match.group(1)
                    logger.info(f"✅ Produto encontrado: {product_id}")

                    # Construir URL limpa do produto
                    product_url = f"https://produto.mercadolivre.com.br/{product_id}"

                    # Usar o link de afiliado original para compartilhamento
                    return (product_url, affiliate_url)

            # Se caiu em página social, tentar extrair do histórico de redirects
            if '/social/' in final_url:
                logger.info("🔍 Detectada página social, buscando URL do produto...")

                # Tentar extrair do parâmetro ref
                parsed = urlparse(final_url)
                params = parse_qs(parsed.query)

                if 'ref' in params:
                    ref_url = unquote(params['ref'][0])
                    product_match = re.search(r'(MLB\d+)', ref_url)
                    if product_match:
                        product_id = product_match.group(1)
                        product_url = f"https://produto.mercadolivre.com.br/{product_id}"
                        logger.info(f"✅ Produto extraído do ref: {product_id}")
                        return (product_url, affiliate_url)

                # Tentar buscar no histórico de redirects
                if hasattr(response, 'history') and response.history:
                    for resp in response.history:
                        if '/p/MLB' in resp.url or re.search(r'/MLB\d+', resp.url):
                            product_match = re.search(r'(MLB\d+)', resp.url)
                            if product_match:
                                product_id = product_match.group(1)
                                product_url = f"https://produto.mercadolivre.com.br/{product_id}"
                                logger.info(f"✅ Produto encontrado no histórico: {product_id}")
                                return (product_url, affiliate_url)

            # Se não conseguiu extrair, retornar a URL final
            logger.warning("⚠️ Não foi possível extrair ID do produto, usando URL final")
            return (final_url, affiliate_url)

        except Exception as e:
            logger.error(f"❌ Erro ao extrair link de afiliado: {e}")
            return (affiliate_url, affiliate_url)

    def _follow_redirect_if_needed(self, url: str) -> str:
        """
        Segue redirects de links curtos de afiliado do ML
        Retorna a URL final do produto
        """
        try:
            # Se for link de afiliado, usar método especializado
            if 'mercadolivre.com/sec/' in url or 'mercadolivre.com.br/sec/' in url or '/s/c/' in url:
                product_url, _ = self._extract_real_affiliate_link(url)
                return product_url

            return url
        except Exception as e:
            logger.warning(f"Erro ao seguir redirect: {e}. Usando URL original.")
            return url

    @cached_scraper
    def scrape_product(self, url: str, affiliate_link: str = "") -> Optional[Dict[str, Any]]:
        try:
            # Determinar se a URL fornecida é um link de afiliado
            is_affiliate_link = ('mercadolivre.com/sec/' in url or
                               'mercadolivre.com.br/sec/' in url or
                               '/s/c/' in url)

            # Se for link de afiliado, extrair URL do produto E manter link de afiliado
            if is_affiliate_link:
                logger.info("🔗 Link de afiliado detectado, extraindo informações...")
                product_url, real_affiliate_link = self._extract_real_affiliate_link(url)
                final_url = product_url
                affiliate_to_use = real_affiliate_link
            else:
                # Se não for link de afiliado, seguir fluxo normal
                final_url = self._follow_redirect_if_needed(url)
                affiliate_to_use = affiliate_link or url

            logger.info(f"📦 Fazendo scraping de: {final_url}")
            logger.info(f"🔗 Link de afiliado a ser usado: {affiliate_to_use[:80]}...")

            # Tentar primeiro com requisição direta (ML geralmente permite)
            response = self.anti_bot.make_request(final_url)
            from bs4 import BeautifulSoup
            # Usar response.text em vez de response.content para lidar com encoding/compression
            soup = BeautifulSoup(response.text, 'html.parser')
            if not soup:
                logger.error("Página de produto não encontrada")
                return None
            product_data = self._extract_product_data(soup, final_url, affiliate_to_use)

            # Verificar se conseguiu extrair dados válidos
            if product_data.get('titulo') == 'Produto sem título' or product_data.get('preco_atual') == 'Preço não disponível':
                logger.warning("Dados incompletos. Tentando via ScraperAPI...")
                try:
                    response = self.anti_bot.make_request_via_api(final_url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    product_data = self._extract_product_data(soup, final_url, affiliate_to_use)
                except Exception as api_error:
                    logger.error(f"ScraperAPI também falhou: {api_error}")

            return self._validate_and_sanitize(product_data)
        except Exception as e:
            logger.error(f"Erro ao fazer scraping do produto ML: {e}")
            return None

    def scrape_search(self, query: str, max_pages: int = 2) -> List[Dict[str, Any]]:
        products = []
        query_formatted = query.replace(' ', '-')
        for page in range(1, max_pages + 1):
            try:
                if page == 1:
                    url = f"{self.config['base_url']}/{query_formatted}"
                else:
                    offset = (page - 1) * self.config['pagination']['step']
                    url = f"{self.config['base_url']}/{query_formatted}_Desde_{offset + 1}"
                # Usar requisição direta primeiro
                response = self.anti_bot.make_request(url)
                from bs4 import BeautifulSoup
                # Usar response.text em vez de response.content para lidar com encoding/compression
                soup = BeautifulSoup(response.text, 'html.parser')
                if not soup:
                    break
                product_items = self.selector.find_elements(soup, 'product_items')
                for item in product_items:
                    try:
                        product_data = self._extract_search_item_data(item)
                        if product_data:
                            validated_data = self._validate_and_sanitize(product_data)
                            products.append(validated_data)
                    except Exception as e:
                        logger.warning(f"Erro ao processar item da busca: {e}")
                        continue
                time.sleep(self.anti_bot.get_page_delay())
            except Exception as e:
                logger.error(f"Erro na página {page} da busca ML: {e}")
                break
        return products

    def _extract_product_data(self, soup, url: str, affiliate_link: str) -> Dict[str, Any]:
        title_elem = self.selector.find_element(soup, 'title')
        title = title_elem.get_text(strip=True) if title_elem else "Produto sem título"

        # Extrair preço de forma mais inteligente
        preco_atual = "Preço não disponível"
        preco_original = None

        # Estratégia 1: Tentar pegar o preço da seção ui-pdp-price (mais confiável)
        price_section = soup.select_one('.ui-pdp-price, .ui-pdp-price__main-container')
        if price_section:
            # Procurar primeiro elemento de preço que não seja riscado
            price_elems = price_section.select('.andes-money-amount:not(.andes-money-amount--previous)')
            if price_elems:
                for price_container in price_elems:
                    fraction = price_container.select_one('.andes-money-amount__fraction')
                    cents = price_container.select_one('.andes-money-amount__cents')

                    if fraction:
                        price_text = fraction.get_text(strip=True)
                        cents_text = f",{cents.get_text(strip=True)}" if cents else ""
                        potential_price = f"R$ {price_text}{cents_text}"

                        # Validar se é um preço real (não parcelamento, etc)
                        parent_classes = ' '.join(price_container.get('class', []))
                        if 'installments' not in parent_classes and price_text.isdigit():
                            preco_atual = potential_price
                            logger.info(f"💰 Preço extraído: {preco_atual}")
                            break

            # Procurar preço original (riscado)
            original_elems = price_section.select('.andes-money-amount--previous .andes-money-amount__fraction, s .andes-money-amount__fraction')
            if original_elems:
                preco_original = f"R$ {original_elems[0].get_text(strip=True)}"

        # Estratégia 2 (fallback): Usar seletores adaptativos
        if preco_atual == "Preço não disponível":
            price_elem = self.selector.find_element(soup, 'price_current')
            price_cents_elem = self.selector.find_element(soup, 'price_cents')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                cents_text = f",{price_cents_elem.get_text(strip=True)}" if price_cents_elem else ""
                preco_atual = f"R$ {price_text}{cents_text}"
                logger.info(f"💰 Preço extraído (fallback): {preco_atual}")

            if not preco_original:
                original_price_elem = self.selector.find_element(soup, 'price_original')
                preco_original = f"R$ {original_price_elem.get_text(strip=True)}" if original_price_elem else None
        
        img_elem = self.selector.find_element(soup, 'image', required=False)
        imagem = ""
        if img_elem:
            # Tentar múltiplos atributos de imagem
            src = (img_elem.get('src') or
                   img_elem.get('data-src') or
                   img_elem.get('data-zoom') or
                   img_elem.get('data-original') or '')
            if src and 'http' in src:
                # Converter para alta resolução e remover parâmetros
                imagem = src.split('?')[0]
                imagem = imagem.replace('-I.jpg', '-O.jpg').replace('-I.webp', '-O.webp')
            else:
                logger.warning(f"Imagem encontrada mas sem src válido: {img_elem}")
        
        loja_elem = self.selector.find_element(soup, 'store_link')
        loja = loja_elem.get_text(strip=True) if loja_elem else ""

        return {
            'titulo': title,
            'link': url,
            'afiliado_link': affiliate_link or url,
            'preco_atual': preco_atual,
            'preco_original': preco_original,
            'imagem': imagem,
            'fonte': 'Mercado Livre',
            'plataforma': 'Mercado Livre',
            'loja': loja
        }

    def _extract_search_item_data(self, item) -> Dict[str, Any]:
        title_elem = self.selector.find_element(item, 'title')
        title = title_elem.get_text(strip=True) if title_elem else ""
        if not title: return None
        
        link_elem = self.selector.find_element(item, 'link')
        link = ""
        if link_elem:
            href = link_elem.get('href', '')
            link = f"https://mercadolivre.com.br{href}" if href.startswith('/') else href

        price_elem = self.selector.find_element(item, 'price_current')
        price_cents_elem = self.selector.find_element(item, 'price_cents')
        preco_atual = "Preço não disponível"
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            cents_text = f",{price_cents_elem.get_text(strip=True)}" if price_cents_elem else ""
            preco_atual = f"R$ {price_text}{cents_text}"

        original_price_elem = self.selector.find_element(item, 'price_original')
        preco_original = f"R$ {original_price_elem.get_text(strip=True)}" if original_price_elem else None
        
        img_elem = self.selector.find_element(item, 'image', required=False)
        imagem = ""
        if img_elem:
            src = (img_elem.get('src') or
                   img_elem.get('data-src') or
                   img_elem.get('data-zoom') or
                   img_elem.get('data-original') or '')
            if src and 'http' in src:
                imagem = src.split('?')[0]
                
        return {
            'titulo': title, 'link': link, 'afiliado_link': link,
            'preco_atual': preco_atual, 'preco_original': preco_original, 'imagem': imagem,
            'fonte': 'Mercado Livre', 'plataforma': 'Mercado Livre'
        }

class AmazonScraper(BaseScraper):
    def __init__(self):
        super().__init__('amazon')

    def scrape_product(self, url: str, affiliate_link: str = "") -> Optional[Dict[str, Any]]:
        try:
            # Usar ScraperAPI para Amazon (mais confiável)
            logger.info(f"Tentando scraping de produto Amazon via ScraperAPI: {url}")
            response = self.anti_bot.make_request_via_api(url)
            from bs4 import BeautifulSoup
            # Usar response.text em vez de response.content para lidar com encoding/compression
            soup = BeautifulSoup(response.text, 'html.parser')
            if not soup:
                logger.error("Página de produto não encontrada via API")
                return None
            product_data = self._extract_product_data(soup, url, affiliate_link)

            # Validar dados extraídos
            if (product_data.get('titulo') == 'Produto sem título' or
                product_data.get('preco_atual') == 'Preço não disponível'):
                logger.warning("Dados incompletos extraídos via API.")
                # Tentar novamente com proxy direto como fallback
                logger.info("Tentando com requisição direta como fallback...")
                try:
                    response = self.anti_bot.make_request(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    product_data = self._extract_product_data(soup, url, affiliate_link)
                except Exception as fallback_error:
                    logger.error(f"Fallback também falhou: {fallback_error}")
                    return self._create_fallback_product(url, affiliate_link)

            return self._validate_and_sanitize(product_data)
        except Exception as e:
            logger.error(f"Erro ao fazer scraping do produto Amazon: {e}")
            return self._create_fallback_product(url, affiliate_link)

    def _create_fallback_product(self, url: str, affiliate_link: str) -> Dict[str, Any]:
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
        asin = asin_match.group(1) if asin_match else "UNKNOWN"
        product_data = {
            'titulo': f"Produto Amazon {asin}",
            'link': url,
            'afiliado_link': affiliate_link or self._generate_affiliate_link(url),
            'preco_atual': "Preço não disponível",
            'plataforma': 'Amazon',
            '_fallback': True,
            '_blocked': True
        }
        return self._validate_and_sanitize(product_data)

    def scrape_search(self, query: str, max_pages: int = 2) -> List[Dict[str, Any]]:
        return amazon_scraping.scrape_amazon(query, max_pages)

    def _extract_product_data(self, soup, url: str, affiliate_link: str) -> Dict[str, Any]:
        title = "Produto sem título"
        title_selectors = ['#productTitle', 'h1.a-size-large', 'h1[data-automation-id="product-title"]']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and len(title_elem.get_text(strip=True)) > 3:
                title = title_elem.get_text(strip=True)
                break

        preco_atual = "Preço não disponível"
        preco_original = None

        # Estratégia 1: Buscar preço usando .a-offscreen (mais confiável)
        preco_atual_selectors = [
            '#corePrice_feature_div .a-price:not(.a-text-price) .a-offscreen',
            '#apex_desktop .a-price .a-offscreen',
            '#corePrice_desktop .a-price .a-offscreen',
            '.a-price.apexPriceToPay .a-offscreen',
            'span.a-price[data-a-size="xl"] .a-offscreen',
            'span.a-price[data-a-size="l"] .a-offscreen',
            '.a-price:not(.a-text-price) .a-offscreen'
        ]

        for selector in preco_atual_selectors:
            elementos = soup.select(selector)
            for elem in elementos:
                # Evitar preços de produtos relacionados/sugeridos
                parent_section = elem.find_parent(['div'], id=lambda x: x and any(
                    keyword in x for keyword in ['similarities', 'bundle', 'btf', 'anonCarousel']
                )) if elem.find_parent(['div']) else None

                if not parent_section:
                    texto = elem.get_text(strip=True)
                    if texto and ('R$' in texto or 'R $' in texto or re.search(r'\d', texto)):
                        preco_atual = amazon_scraping.sanitize_amazon_price(texto)
                        logger.info(f"💰 Preço atual encontrado: {preco_atual}")
                        break

            if preco_atual != "Preço não disponível":
                break

        # Estratégia 2: Se não encontrou, tentar construir a partir de partes
        if preco_atual == "Preço não disponível":
            price_containers = soup.select('#corePrice_feature_div .a-price, #apex_desktop .a-price, #corePrice_desktop .a-price')
            for container in price_containers:
                # Verificar se não é preço riscado
                if 'a-text-price' in container.get('class', []):
                    continue

                whole_elem = container.select_one('.a-price-whole')
                fraction_elem = container.select_one('.a-price-fraction')

                if whole_elem:
                    symbol = container.select_one('.a-price-symbol')
                    symbol_text = symbol.get_text(strip=True) if symbol else 'R$'
                    whole = whole_elem.get_text(strip=True)
                    fraction = fraction_elem.get_text(strip=True) if fraction_elem else "00"

                    # Validar número
                    whole_clean = re.sub(r'[^\d]', '', whole)
                    if whole_clean and whole_clean.isdigit():
                        preco_atual = amazon_scraping.format_amazon_price(symbol_text, whole, fraction)
                        logger.info(f"💰 Preço atual construído: {preco_atual}")
                        break

        # Estratégia 3: Buscar preço original (riscado)
        preco_original_selectors = [
            '.basisPrice .a-offscreen',
            '.a-price.a-text-price .a-offscreen',
            'span[data-a-strike="true"] .a-offscreen',
            '.a-price-was .a-offscreen',
            's .a-offscreen'
        ]

        for selector in preco_original_selectors:
            elementos = soup.select(selector)
            for elem in elementos:
                texto = elem.get_text(strip=True)
                if texto and texto != preco_atual:
                    preco_sanitizado = amazon_scraping.sanitize_amazon_price(texto)
                    if preco_sanitizado and preco_sanitizado != preco_atual:
                        preco_original = preco_sanitizado
                        logger.info(f"💰 Preço original encontrado: {preco_original}")
                        break

            if preco_original:
                break

        imagem = ""
        img_elem = soup.select_one('#landingImage, #imgTagWrapperId img')
        if img_elem:
            if img_elem.has_attr('data-a-dynamic-image'):
                import json
                try:
                    img_data = json.loads(img_elem['data-a-dynamic-image'])
                    imagem = list(img_data.keys())[0]
                except: pass
            else:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src and 'http' in src:
                    imagem = src

        return {
            'titulo': title, 'link': url, 'afiliado_link': affiliate_link or self._generate_affiliate_link(url),
            'preco_atual': preco_atual, 'preco_original': preco_original, 'imagem': imagem,
            'fonte': 'Amazon', 'plataforma': 'Amazon'
        }

    def _generate_affiliate_link(self, url: str) -> str:
        # ... (código existente)
        return url

class ScraperFactory:
    _scrapers = {
        'mercadolivre': MercadoLivreScraper,
        'amazon': AmazonScraper,
    }

    @classmethod
    def create_scraper(cls, platform: str) -> Optional[BaseScraper]:
        platform = platform.lower()
        if platform in cls._scrapers:
            return cls._scrapers[platform]()
        logger.error(f"Scraper não encontrado para plataforma: {platform}")
        return None

    @classmethod
    def get_available_platforms(cls) -> List[str]:
        return list(cls._scrapers.keys())

    @classmethod
    def detect_platform_from_url(cls, url: str) -> Optional[str]:
        return ScrapingConfig.detect_platform(url)