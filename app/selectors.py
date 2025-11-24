# /app/selectors.py
"""
Sistema de seletores adaptativos para mudanças de layout
"""
import logging
from typing import Dict, List
from .config import ScrapingConfig

logger = logging.getLogger(__name__)

class AdaptiveSelector:
    """Sistema de seletores adaptativos para mudanças de layout"""

    def __init__(self, platform: str):
        self.platform = platform
        self.config = ScrapingConfig.get_platform_config(platform)
        self.fallback_selectors = self._get_fallback_selectors()

    def _get_fallback_selectors(self) -> Dict[str, List[str]]:
        """Retorna seletores alternativos para cada elemento"""
        fallbacks = {
            'mercadolivre': {
                'product_items': ['li.ui-search-layout__item'],
                'title': ['a.poly-component__title', 'h3.poly-component__title-wrapper', 'h1.ui-pdp-title', 'h2.ui-search-item__title'],
                'link': ['a.poly-component__title', 'a.ui-search-link'],
                'price_current': ['.poly-price__current .andes-money-amount__fraction', '.andes-money-amount__fraction'],
                'price_cents': ['.poly-price__current .andes-money-amount__cents', '.andes-money-amount__cents'],
                'price_original': ['s .andes-money-amount__fraction', '.ui-pdp-price__original-value .andes-money-amount__fraction', '.poly-price__previous .andes-money-amount__fraction'],
                'image': [
                    'img.ui-pdp-image',
                    'img.ui-pdp-gallery__figure__image',
                    '.ui-pdp-gallery__figure img',
                    'img[data-zoom]',
                    'figure.ui-pdp-gallery__figure img',
                    'img.poly-component__picture',
                    'img.ui-search-result-image__element'
                ],
                'store_link': ['.ui-pdp-seller__link-trigger']
            },
            'amazon': {
                'product_items': ['[data-component-type="s-search-result"]'],
                'title': ['h2 .a-text-normal', '#productTitle'],
                'link': ['h2 a'],
                'price_current': ['.a-price .a-offscreen'],
                'image': ['img.s-image']
            },
            'shopee': {
                'product_items': ['.shopee-search-item-result__item'],
                'title': ['._44qnta', 'div[data-sqe="name"] > div > div'],
                'link': ['a'],
                'price_current': ['._3_Fivj', '._2_BY_8'],
                'price_original': ['._2_BY_8'],
                'image': ['._39-Tsj ._12_1rN', 'img.shopee-image__content'],
                'store': ['._3_0f-8']
            }
        }
        
        return fallbacks.get(self.platform, {})
    
    def find_element(self, soup, element_type: str, required: bool = True):
        """Encontra elemento usando seletores adaptativos"""
        selectors = []
        if self.config and 'selectors' in self.config and element_type in self.config['selectors']:
             selectors.append(self.config['selectors'].get(element_type, ''))
        selectors.extend(self.fallback_selectors.get(element_type, []))
        
        for selector in selectors:
            if not selector: continue
            try:
                element = soup.select_one(selector)
                if element:
                    return element
            except Exception as e:
                logger.warning(f"Erro ao usar seletor {selector}: {e}")
                continue
        
        if required:
            logger.error(f"Elemento {element_type} não encontrado com nenhum seletor")
        
        return None
    
    def find_elements(self, soup, element_type: str) -> List:
        """Encontra múltiplos elementos usando seletores adaptativos"""
        selectors = []
        if self.config and 'selectors' in self.config and element_type in self.config['selectors']:
             selectors.append(self.config['selectors'].get(element_type, ''))
        selectors.extend(self.fallback_selectors.get(element_type, []))

        logger.debug(f"Procurando elementos tipo '{element_type}' com seletores: {selectors}")

        for selector in selectors:
            if not selector: continue
            try:
                elements = soup.select(selector)
                logger.debug(f"Seletor '{selector}' encontrou {len(elements)} elementos")
                if elements:
                    return elements
            except Exception as e:
                logger.warning(f"Erro ao usar seletor {selector}: {e}")
                continue

        logger.warning(f"Nenhum elemento encontrado para tipo '{element_type}'")
        return []