# app/ml_affiliate.py
"""
Módulo para geração de links de afiliados do Mercado Livre usando a API interna.
"""

import os
import logging
import requests
from typing import Optional, Dict
import json
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class MercadoLivreAffiliate:
    """Classe para gerenciar geração de links de afiliados do Mercado Livre"""

    def __init__(self):
        # Endpoints possíveis da API do ML - ORDENADOS POR PRIORIDADE (mais provável de funcionar primeiro)
        self.endpoints = [
            "https://www.mercadolivre.com.br/affiliate-program/api/v2/affiliates/createLink",  # Mais comum
            "https://www.mercadolivre.com.br/affiliate-program/api/affiliates/createLink",
            "https://www.mercadolivre.com.br/affiliate-program/api/v2/stripe/user/links"
        ]
        self.affiliate_tag = os.getenv("MERCADOLIVRE_AFFILIATE_ID", "gabrielvilelaluiz")

        # Cookies de sessão (devem ser configurados nas variáveis de ambiente)
        self.cookies = self._get_cookies_from_env()
        self.csrf_token = os.getenv("ML_CSRF_TOKEN", "")

        # Cache da combinação que funciona (endpoint + payload index)
        self._working_combination = None

        # Cache de falhas para evitar testar combinações que sabemos que não funcionam
        self._failed_combinations = set()

    def _get_cookies_from_env(self) -> Dict[str, str]:
        """Extrai cookies de sessão das variáveis de ambiente"""
        cookies = {}

        # Lista de cookies importantes para autenticação
        cookie_names = [
            "_csrf",
            "orgnickp",
            "orguseridp",
            "orguserid",
            "_mldataSessionId",
            "_d2id",
            "ssid",
            "ftid",
            "nsa_rotok",
            "x_meli_session_id",
            "cp",
            "c_ctid",
            "c_ids"
        ]

        for cookie_name in cookie_names:
            env_key = f"ML_COOKIE_{cookie_name.upper()}"
            cookie_value = os.getenv(env_key, "")
            if cookie_value:
                # Alguns cookies têm hífens, converter para underscore
                actual_cookie_name = cookie_name.replace("_", "-") if cookie_name.startswith("x_") else cookie_name
                cookies[actual_cookie_name] = cookie_value

        # Também aceita uma string completa de cookies
        cookies_string = os.getenv("ML_COOKIES", "")
        if cookies_string:
            for cookie_pair in cookies_string.split(";"):
                if "=" in cookie_pair:
                    key, value = cookie_pair.strip().split("=", 1)
                    cookies[key] = value

        # Avisar se não há cookies configurados
        if not cookies:
            logger.warning('⚠️ COOKIES DO MERCADO LIVRE NÃO CONFIGURADOS!')
            logger.warning('📝 Configure os cookies no arquivo .env para gerar links de afiliado.')
            logger.warning('📚 Veja instruções em: .env.example')

        return cookies

    def _try_generate_link(self, endpoint: str, payload: dict, headers: dict) -> Optional[str]:
        """
        Tenta gerar link usando um endpoint e payload específicos.

        Returns:
            Link de afiliado ou None se falhar
        """
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                cookies=self.cookies,
                timeout=5  # Reduzido de 10s para 5s para maior velocidade
            )

            # Verificar se a requisição foi bem-sucedida
            if response.status_code in [200, 201]:
                response_data = response.json()

                # Tentar extrair o link de diferentes formatos de resposta
                affiliate_link = None

                # Formato 1: { "short_url": "..." } ← FORMATO CORRETO DO ML!
                if isinstance(response_data, dict) and 'short_url' in response_data:
                    affiliate_link = response_data['short_url']

                # Formato 2: { "link": "..." }
                elif isinstance(response_data, dict) and 'link' in response_data:
                    affiliate_link = response_data['link']

                # Formato 3: { "data": { "link": "..." } }
                elif isinstance(response_data, dict) and 'data' in response_data:
                    if isinstance(response_data['data'], dict) and 'link' in response_data['data']:
                        affiliate_link = response_data['data']['link']

                # Formato 4: { "url": "..." }
                elif isinstance(response_data, dict) and 'url' in response_data:
                    affiliate_link = response_data['url']

                # Formato 5: { "shortUrl": "..." } (camelCase)
                elif isinstance(response_data, dict) and 'shortUrl' in response_data:
                    affiliate_link = response_data['shortUrl']

                # Formato 6: { "affiliateLink": "..." }
                elif isinstance(response_data, dict) and 'affiliateLink' in response_data:
                    affiliate_link = response_data['affiliateLink']

                if affiliate_link:
                    logger.info(f'✅ API retornou link: {affiliate_link}')
                else:
                    logger.warning(f'⚠️ API retornou 200 mas sem link válido. Response: {response_data}')

                return affiliate_link

            elif response.status_code == 401:
                logger.error('❌ Erro 401: Cookies expirados ou inválidos')
                logger.error('📝 Renove os cookies no .env seguindo: CONFIGURAR_COOKIES_ML.md')
                return None

            elif response.status_code == 403:
                logger.error('❌ Erro 403: Sem permissão')
                return None

            elif response.status_code == 404:
                return None

        except requests.exceptions.JSONDecodeError:
            return None
        except Exception:
            return None

        return None

    def generate_affiliate_link(self, product_url: str) -> Optional[str]:
        """
        Gera um link de afiliado usando a API interna do Mercado Livre.

        Args:
            product_url: URL do produto do Mercado Livre

        Returns:
            Link de afiliado encurtado ou None em caso de erro
        """
        try:
            # Verificar se temos as credenciais necessárias
            if not self.cookies or not self.csrf_token:
                logger.warning('⚠️ Cookies ou CSRF token do ML não configurados. Usando método tradicional (mshops).')
                return None

            if not self.affiliate_tag:
                logger.warning('⚠️ MERCADOLIVRE_AFFILIATE_ID não configurado.')
                return None

            # Validar se é um link do Mercado Livre
            if 'mercadolivre.com' not in product_url.lower() and 'mercadolibre.com' not in product_url.lower():
                logger.warning(f'⚠️ URL não é do Mercado Livre: {product_url}')
                return None

            logger.info(f'🔗 Gerando link de afiliado ML via API para: {product_url[:80]}...')

            # Preparar headers
            headers = {
                'Content-Type': 'application/json',
                'X-CSRF-Token': self.csrf_token,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                'Referer': 'https://www.mercadolivre.com.br/affiliate-program/dashboard',
                'Origin': 'https://www.mercadolivre.com.br',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'x-platform': 'ml',
                'x-device-js': 'true'
            }

            # Preparar diferentes formatos de payload - ORDENADOS POR PRIORIDADE
            # Com base no histórico, o formato 2 (com tag) é o que mais funciona
            payloads_to_try = [
                # Formato 1: Com tag de afiliado (MAIS COMUM QUE FUNCIONA)
                {
                    "url": product_url,
                    "tag": self.affiliate_tag
                },

                # Formato 2: Completo com SHORT_URL
                {
                    "url": product_url,
                    "tag": self.affiliate_tag,
                    "linkType": "SHORT_URL"
                },

                # Formato 3: Simples com URL
                {"url": product_url},

                # Formato 4: Com tipo SHORT_URL
                {
                    "url": product_url,
                    "linkType": "SHORT_URL"
                }
            ]

            # Se já temos uma combinação que funcionou antes, tentar ela primeiro
            if self._working_combination:
                endpoint_idx, payload_idx = self._working_combination
                try:
                    result = self._try_generate_link(
                        self.endpoints[endpoint_idx],
                        payloads_to_try[payload_idx],
                        headers
                    )
                    if result:
                        logger.info(f'✅ Link gerado (cache): {result}')
                        return result
                    else:
                        # Cache inválido, limpar
                        self._working_combination = None
                except Exception:
                    # Cache inválido, limpar
                    self._working_combination = None

            # Tentar diferentes endpoints e payloads
            for endpoint_idx, endpoint in enumerate(self.endpoints):
                for payload_idx, payload in enumerate(payloads_to_try):
                    # Pular combinações que já falharam antes
                    combo_key = (endpoint_idx, payload_idx)
                    if combo_key in self._failed_combinations:
                        continue

                    result = self._try_generate_link(endpoint, payload, headers)
                    if result:
                        # Salvar combinação que funcionou
                        self._working_combination = (endpoint_idx, payload_idx)
                        logger.info(f'✅ Link gerado: {result}')
                        return result
                    else:
                        # Marcar como falha para não tentar de novo
                        self._failed_combinations.add(combo_key)

            # Se nenhum endpoint/payload funcionou
            logger.warning('⚠️ API não disponível. Usando método tradicional (mshops).')
            return None

        except requests.exceptions.Timeout:
            logger.error('❌ Timeout ao tentar gerar link de afiliado via API do ML')
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f'❌ Erro de conexão ao gerar link de afiliado: {str(e)}')
            return None

        except Exception as e:
            logger.error(f'❌ Erro inesperado ao gerar link de afiliado: {str(e)}')
            import traceback
            logger.error(traceback.format_exc())
            return None

    def is_configured(self) -> bool:
        """Verifica se as credenciais estão configuradas"""
        return bool(self.cookies and self.csrf_token and self.affiliate_tag)


# Instância global para uso fácil
ml_affiliate = MercadoLivreAffiliate()


def expandir_link_curto_ml(short_url: str) -> Optional[str]:
    """
    Expande um link curto de afiliado do Mercado Livre (https://mercadolivre.com/sec/...)
    acessando a página social e extraindo o link real do produto.

    Isso permite "clonar eticamente" - você visita o link de afiliado do criador original
    (gerando comissão para ele), e depois cria seu próprio link de afiliado.

    Args:
        short_url: Link curto de afiliado (ex: https://mercadolivre.com/sec/1citUM9)

    Returns:
        URL real do produto ou None se falhar
    """
    try:
        # Validar se é realmente um link curto ML
        if not ('mercadolivre.com/sec/' in short_url or 'mercadolibre.com/sec/' in short_url):
            logger.warning(f'⚠️ URL não é um link curto ML: {short_url}')
            return None

        logger.info(f'🔗 Expandindo link curto ML: {short_url}')

        # Headers para simular navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.mercadolivre.com.br/',
        }

        # PASSO 1: Acessar o link curto (gera comissão para o criador original)
        response = requests.get(short_url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()

        logger.info(f'✅ Link acessado. URL final: {response.url[:100]}...')

        # PASSO 2: Parsear HTML da página social
        soup = BeautifulSoup(response.content, 'html.parser')

        # PASSO 3: Buscar o botão "Ir para o produto" usando múltiplos seletores
        product_link = None

        # Seletores possíveis para o link do produto
        seletores = [
            # Seletor específico fornecido pelo usuário
            '#root-app > div > div > div.rl-social-desktop_container > div.rl-social-desktop_content > section > section > section > div > ul > div > div.poly-card__content > div.poly-content > div:nth-child(2) > div > div > a',

            # Seletores alternativos mais genéricos
            'a[href*="/p/MLB"]',  # Links de produto (/p/MLB...)
            'a[href*="/MLB-"]',   # Links de produto (/MLB-...)
            '.poly-card__content a[href*="MLB"]',
            '.poly-content a[href*="MLB"]',
            'a.andes-button--loud',  # Botões principais
            'a[data-testid="product-link"]',
            'a.ui-pdp-action-modal__link',
        ]

        for seletor in seletores:
            element = soup.select_one(seletor)
            if element and element.get('href'):
                href = element.get('href')

                # Validar se é realmente um link de produto
                if '/p/MLB' in href or '/MLB-' in href:
                    # Construir URL completa se for relativa
                    if href.startswith('http'):
                        product_link = href
                    else:
                        product_link = f"https://www.mercadolivre.com.br{href}"

                    logger.info(f'✅ Link do produto encontrado usando seletor: {seletor}')
                    logger.info(f'   URL: {product_link}')
                    break

        # PASSO 4: Se não encontrou com seletores, buscar em todos os links
        if not product_link:
            logger.warning('⚠️ Seletores não encontraram o link. Buscando em todos os links...')

            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                if ('/p/MLB' in href or '/MLB-' in href) and 'mercadolivre.com.br' in href:
                    # Limpar parâmetros desnecessários
                    product_link = href.split('#')[0].split('?')[0]
                    if product_link.startswith('http'):
                        logger.info(f'✅ Link do produto encontrado (busca geral): {product_link}')
                        break

        # PASSO 5: Limpar URL do produto (remover parâmetros de afiliado)
        if product_link:
            # Remover parâmetros de rastreamento/afiliado do link original
            product_link = re.sub(r'[?&]pdp_filters.*', '', product_link)
            product_link = re.sub(r'[?&]tracking_id.*', '', product_link)
            product_link = re.sub(r'[?&]c_id.*', '', product_link)
            product_link = re.sub(r'[?&]c_uid.*', '', product_link)
            product_link = product_link.split('#')[0]  # Remover âncoras

            logger.info(f'✅ Link do produto limpo: {product_link}')
            return product_link

        logger.warning('❌ Não foi possível encontrar o link do produto na página social')
        return None

    except requests.exceptions.Timeout:
        logger.error('❌ Timeout ao acessar link curto ML')
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f'❌ Erro ao acessar link curto ML: {str(e)}')
        return None

    except Exception as e:
        logger.error(f'❌ Erro inesperado ao expandir link curto ML: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return None


def gerar_link_afiliado_ml(product_url: str) -> Optional[str]:
    """
    Função auxiliar para gerar link de afiliado do Mercado Livre.

    Args:
        product_url: URL do produto

    Returns:
        Link de afiliado ou None se falhar
    """
    return ml_affiliate.generate_affiliate_link(product_url)
