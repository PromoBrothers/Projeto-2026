import time
import random
import requests
import os
from typing import Dict, Optional, List, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
import threading
from collections import defaultdict
from .config import ScrapingConfig

logger = logging.getLogger(__name__)

class RateLimiter:
    """Limitador de taxa para evitar sobrecarga em requisições em massa"""
    def __init__(self, max_requests_per_minute: int = 30):
        self.max_requests = max_requests_per_minute
        self.requests_by_domain = defaultdict(list)
        self.lock = threading.Lock()

    def wait_if_needed(self, domain: str):
        """Aguarda se necessário para respeitar o rate limit"""
        with self.lock:
            now = time.time()
            # Remover requisições antigas (mais de 60 segundos)
            self.requests_by_domain[domain] = [
                req_time for req_time in self.requests_by_domain[domain]
                if now - req_time < 60
            ]

            # Verificar se atingiu o limite
            if len(self.requests_by_domain[domain]) >= self.max_requests:
                oldest_request = self.requests_by_domain[domain][0]
                wait_time = 60 - (now - oldest_request)
                if wait_time > 0:
                    logger.warning(f"Rate limit atingido para {domain}. Aguardando {wait_time:.1f}s")
                    time.sleep(wait_time)
                    # Limpar lista após esperar
                    self.requests_by_domain[domain] = []

            # Registrar esta requisição
            self.requests_by_domain[domain].append(time.time())

class ProxyManager:
    def __init__(self):
        self.proxies: List[Dict[str, str]] = []
        self.current_proxy_index = 0
        self.failed_proxies: set = set()
        self._load_proxies()

    def _load_proxies(self):
        main_proxy = ScrapingConfig.get_proxy_config()
        if main_proxy:
            self.proxies.append(main_proxy)
        additional_proxies = self._get_additional_proxies()
        self.proxies.extend(additional_proxies)

    def _get_additional_proxies(self) -> List[Dict[str, str]]:
        additional = []
        proxy2_host = os.getenv("PROXY2_HOST")
        proxy2_port = os.getenv("PROXY2_PORT")
        proxy2_user = os.getenv("PROXY2_USERNAME")
        proxy2_pass = os.getenv("PROXY2_PASSWORD")
        if all([proxy2_host, proxy2_port, proxy2_user, proxy2_pass]):
            proxy_url = f"http://{proxy2_user}:{proxy2_pass}@{proxy2_host}:{proxy2_port}"
            additional.append({'http': proxy_url, 'https': proxy_url})
        return additional

    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        if not self.proxies:
            return None
        available_proxies = [p for i, p in enumerate(self.proxies) if i not in self.failed_proxies]
        if not available_proxies:
            self.failed_proxies.clear()
            available_proxies = self.proxies
        if available_proxies:
            proxy = random.choice(available_proxies)
            self.current_proxy_index = self.proxies.index(proxy)
            return proxy
        return None

    def mark_proxy_failed(self, proxy: Dict[str, str]):
        try:
            index = self.proxies.index(proxy)
            self.failed_proxies.add(index)
        except ValueError:
            pass

class AntiBotManager:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.scraperapi_key = os.getenv("SCRAPERAPI_KEY")
        self.rate_limiter = RateLimiter(max_requests_per_minute=30)

    def _create_fresh_session(self):
        """Cria uma nova sessão HTTP para evitar problemas de estado entre requisições"""
        session = requests.Session()
        retry_strategy = Retry(
            total=ScrapingConfig.RETRY_CONFIG['max_retries'],
            backoff_factor=ScrapingConfig.RETRY_CONFIG['backoff_factor'],
            status_forcelist=ScrapingConfig.RETRY_CONFIG['status_forcelist'],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def get_request_config(self) -> Tuple[Dict[str, str], Optional[Dict[str, str]]]:
        headers = ScrapingConfig.get_random_headers()
        proxy = self.proxy_manager.get_next_proxy()
        return headers, proxy

    def make_request_via_api(self, url: str, **kwargs) -> requests.Response:
        if not self.scraperapi_key:
            logger.warning("SCRAPERAPI_KEY não configurada. Usando requisição direta.")
            return self.make_request(url, **kwargs)

        api_url = 'http://api.scraperapi.com'
        payload = {'api_key': self.scraperapi_key, 'url': url, 'render': 'true'}
        logger.info(f"Fazendo requisição para {url} via ScraperAPI...")

        # Criar uma sessão fresca para cada requisição via API
        session = self._create_fresh_session()
        try:
            response = session.get(api_url, params=payload, timeout=90)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao fazer requisição via ScraperAPI: {e}")
            logger.warning("Tentando requisição direta como fallback...")
            return self.make_request(url, **kwargs)
        finally:
            # Fechar a sessão após o uso
            session.close()

    def make_request(self, url: str, **kwargs) -> requests.Response:
        max_attempts = 3
        session = None

        # Extrair domínio para rate limiting
        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        # Aplicar rate limiting por domínio
        self.rate_limiter.wait_if_needed(domain)

        for attempt in range(max_attempts):
            # Criar uma sessão fresca para cada tentativa
            session = self._create_fresh_session()

            try:
                headers, proxy = self.get_request_config()
                delay = random.uniform(
                    ScrapingConfig.DELAY_CONFIG['min_delay'],
                    ScrapingConfig.DELAY_CONFIG['max_delay']
                )
                time.sleep(delay)
                response = session.get(
                    url,
                    headers=headers,
                    proxies=proxy,
                    timeout=ScrapingConfig.RETRY_CONFIG['timeout'],
                    **kwargs
                )
                if self._is_blocked(response):
                    logger.warning(f"Possível bloqueio detectado na tentativa {attempt + 1}")
                    if proxy:
                        self.proxy_manager.mark_proxy_failed(proxy)
                    if attempt < max_attempts - 1:
                        session.close()
                        time.sleep(ScrapingConfig.DELAY_CONFIG['retry_delay'])
                        continue
                # Não fechar a sessão aqui, pois o response ainda precisa dela
                return response
            except requests.exceptions.ProxyError:
                if proxy:
                    self.proxy_manager.mark_proxy_failed(proxy)
                logger.warning(f"Erro de proxy na tentativa {attempt + 1}")
                session.close()
            except requests.exceptions.RequestException as e:
                logger.error(f"Erro na requisição: {e}")
                session.close()

            if attempt < max_attempts - 1:
                time.sleep(ScrapingConfig.DELAY_CONFIG['retry_delay'])

        raise requests.exceptions.RequestException("Todas as tentativas falharam")

    def _is_blocked(self, response: requests.Response) -> bool:
        if response.status_code in [403, 429, 503]:
            return True
        content_lower = response.text.lower()
        blocked_indicators = [
            'access denied', 'blocked', 'captcha', 'cloudflare', 'rate limit',
            'too many requests', 'robot', 'bot detection', 'suspicious activity',
            'please verify', 'security check', 'unusual traffic'
        ]
        return any(indicator in content_lower for indicator in blocked_indicators)

    def get_page_delay(self) -> float:
        return random.uniform(
            ScrapingConfig.DELAY_CONFIG['page_delay'],
            ScrapingConfig.DELAY_CONFIG['page_delay'] * 1.5
        )