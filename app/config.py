# /app/config.py
"""
Configurações centralizadas para o sistema de web scraping
"""

import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
import random

load_dotenv()

class ScrapingConfig:
    """Configurações para web scraping"""
    
    # User Agents realistas para rotacionar
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    # Headers base mais completos para simular um navegador real
    BASE_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',  # Removido 'br' pois requests não suporta Brotli sem dependência adicional
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    # Configurações de proxy
    PROXY_CONFIG = {
        'host': os.getenv("PROXY_HOST"),
        'port': os.getenv("PROXY_PORT"),
        'username': os.getenv("PROXY_USERNAME"),
        'password': os.getenv("PROXY_PASSWORD"),
        'enabled': os.getenv("USE_PROXY", "true").lower() == "true"
    }
    
    # Configurações de delay
    DELAY_CONFIG = {
        'min_delay': 1.0,
        'max_delay': 3.0,
        'page_delay': 2.0,
        'retry_delay': 5.0
    }
    
    # Configurações de retry
    RETRY_CONFIG = {
        'max_retries': 3,
        'backoff_factor': 2,
        'status_forcelist': [500, 502, 503, 504, 429],
        'timeout': 30
    }
    
    # Configurações de cache
    CACHE_CONFIG = {
        'enabled': True,
        'ttl': 3600,  # 1 hora
        'max_size': 1000
    }
    
    # Configurações de plataformas (mantém o que você já tem)
    PLATFORM_CONFIGS = {
        'mercadolivre': {
            'base_url': 'https://lista.mercadolivre.com.br',
            'pagination': {
                'step': 50,
                'param_name': '_Desde_'
            },
            'selectors': {
                'product_items': 'li.ui-search-layout__item',
                'title': 'a.poly-component__title',
                'link': 'a.poly-component__title',
                'price_current': '.andes-money-amount__fraction',
                'price_cents': '.andes-money-amount__cents',
                'price_original': 's .andes-money-amount__fraction',
                'image': 'img.poly-component__picture',
                'store_link': '.ui-pdp-seller__link-trigger'
            }
        },
        'amazon': {
            'base_url': 'https://www.amazon.com.br',
            'search_url': 'https://www.amazon.com.br/s',
            # ... resto da configuração da Amazon
        },
        'shopee': {
            'base_url': 'https://shopee.com.br',
            'search_url': 'https://shopee.com.br/search',
            'selectors': {
                'product_items': '.shopee-search-item-result__item',
                'title': '._44qnta',
                'link': 'a',
                'price_current': '._3_Fivj',
                'price_original': '._2_BY_8',
                'image': '._39-Tsj ._12_1rN',
                'store': '._3_0f-8'
            }
        },
    }
    
    # IDs de afiliado - Configure no arquivo .env
    AFFILIATE_IDS = {
        'amazon': os.getenv("AMAZON_ASSOCIATES_TAG", "promobrothers-20"),
        'mercadolivre': os.getenv("MERCADOLIVRE_AFFILIATE_ID", ""),
        'shopee': os.getenv("SHOPEE_AFFILIATE_ID", ""),
        'magazineluiza': os.getenv("MAGAZINELUIZA_AFFILIATE_ID", ""),
        'americanas': os.getenv("AMERICANAS_AFFILIATE_ID", ""),
        'casasbahia': os.getenv("CASASBAHIA_AFFILIATE_ID", ""),
    }
    
    @classmethod
    def get_random_headers(cls) -> Dict[str, str]:
        """Retorna headers aleatórios com User-Agent realista"""
        headers = cls.BASE_HEADERS.copy()
        headers['User-Agent'] = random.choice(cls.USER_AGENTS)
        return headers
    
    @classmethod
    def get_proxy_config(cls) -> Optional[Dict[str, str]]:
        """Retorna configuração de proxy se disponível"""
        if not cls.PROXY_CONFIG['enabled']:
            return None
            
        if all([cls.PROXY_CONFIG['host'], cls.PROXY_CONFIG['port'], 
                cls.PROXY_CONFIG['username'], cls.PROXY_CONFIG['password']]):
            proxy_url = f"http://{cls.PROXY_CONFIG['username']}:{cls.PROXY_CONFIG['password']}@{cls.PROXY_CONFIG['host']}:{cls.PROXY_CONFIG['port']}"
            return {
                'http': proxy_url,
                'https': proxy_url
            }
        return None
    
    @classmethod
    def get_platform_config(cls, platform: str) -> Optional[Dict]:
        """Retorna configuração específica da plataforma"""
        return cls.PLATFORM_CONFIGS.get(platform.lower())
    
    @classmethod
    def detect_platform(cls, url: str) -> Optional[str]:
        """Detecta a plataforma baseada na URL"""
        url_lower = url.lower()
        
        if 'mercadolivre.com' in url_lower or 'mercadolibre.com' in url_lower:
            return 'mercadolivre'
        elif 'amazon.com' in url_lower or 'amzn.to' in url_lower:
            return 'amazon'
        elif 'shopee.com.br' in url_lower:
            return 'shopee'
        # ... resto da detecção

        return None