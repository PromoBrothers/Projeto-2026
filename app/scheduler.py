# app/scheduler.py
"""
Sistema de agendamento automático de mensagens do WhatsApp.
Processa produtos agendados e envia para os grupos configurados.
"""

import logging
import sys
import time
import threading
from datetime import datetime, timedelta
import pytz
import requests
import os
from typing import List, Dict, Optional

# Configurar logging para UTF-8 (fix para emojis no Windows)
logger = logging.getLogger(__name__)

# Tentar configurar UTF-8 para evitar erro com emojis
try:
    # Python 3.7+
    handler = logging.StreamHandler(sys.stderr)
    handler.stream.reconfigure(encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
except (AttributeError, Exception):
    # Fallback: usar handler padrão sem emojis
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

class MessageScheduler:
    """Classe para gerenciar agendamento e envio automático de mensagens"""

    def __init__(self):
        self.running = False
        self.thread = None
        self.check_interval = 30  # Verificar a cada 30 segundos
        self.whatsapp_url = os.getenv('WHATSAPP_MONITOR_URL', 'http://qrcode:3001')
        self.timezone = pytz.timezone('America/Sao_Paulo')

    def start(self):
        """Inicia o scheduler em uma thread separada"""
        if self.running:
            logger.warning('⚠️ Scheduler já está rodando')
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info('✅ Scheduler de mensagens iniciado')

    def stop(self):
        """Para o scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info('🛑 Scheduler de mensagens parado')

    def _run(self):
        """Loop principal do scheduler"""
        logger.info('🔄 Scheduler rodando... Verificando mensagens agendadas a cada 30s')

        while self.running:
            try:
                self._check_and_send_scheduled_messages()
            except Exception as e:
                logger.error(f'❌ Erro no scheduler: {e}')
                import traceback
                logger.error(traceback.format_exc())

            # Aguardar antes da próxima verificação
            time.sleep(self.check_interval)

    def _check_and_send_scheduled_messages(self):
        """Verifica e envia mensagens que chegaram no horário agendado"""
        from . import database

        try:
            # Buscar produtos agendados
            produtos = database.listar_produtos_db('agendado', 'asc')

            if not produtos:
                return

            now = datetime.now(self.timezone)

            for produto in produtos:
                agendamento_str = produto.get('agendamento')
                if not agendamento_str:
                    continue

                try:
                    # Converter agendamento para datetime
                    agendamento_dt = datetime.fromisoformat(agendamento_str.replace('Z', '+00:00'))
                    agendamento_dt = agendamento_dt.astimezone(self.timezone)

                    # Verificar se já passou do horário agendado
                    if now >= agendamento_dt:
                        logger.info(f'⏰ Horário atingido para produto: {produto.get("titulo", "")[:50]}...')

                        # Enviar mensagem
                        self._send_scheduled_message(produto)

                        # Remover agendamento (não atualizar enviado_em pois coluna não existe)
                        database.atualizar_produto_db(
                            produto['id'],
                            {'agendamento': None}
                        )

                        logger.info(f'✅ Mensagem enviada e agendamento removido: {produto["id"]}')

                except Exception as e:
                    logger.error(f'❌ Erro ao processar produto {produto.get("id")}: {e}')

        except Exception as e:
            logger.error(f'❌ Erro ao verificar mensagens agendadas: {e}')

    def _send_scheduled_message(self, produto: Dict) -> bool:
        """Envia mensagem agendada para o WhatsApp"""
        try:
            # Verificar se WhatsApp está conectado
            if not self._check_whatsapp_connection():
                logger.warning('⚠️ WhatsApp não está conectado. Pulando envio.')
                return False

            # Obter grupos configurados para envio automático
            grupos_destino = self._get_target_groups()

            if not grupos_destino:
                logger.warning('⚠️ Nenhum grupo configurado para envio automático')
                return False

            # Montar mensagem
            mensagem = produto.get('final_message', '')
            imagem_url = produto.get('processed_image_url') or produto.get('imagem_url')

            if not mensagem:
                logger.error('❌ Produto sem mensagem formatada')
                return False

            # Enviar para cada grupo
            sucesso = True
            for grupo_id in grupos_destino:
                try:
                    self._send_to_whatsapp(grupo_id, mensagem, imagem_url)
                    logger.info(f'✅ Enviado para grupo: {grupo_id}')
                    time.sleep(2)  # Delay entre envios
                except Exception as e:
                    logger.error(f'❌ Erro ao enviar para {grupo_id}: {e}')
                    sucesso = False

            return sucesso

        except Exception as e:
            logger.error(f'❌ Erro ao enviar mensagem agendada: {e}')
            return False

    def _check_whatsapp_connection(self) -> bool:
        """Verifica se o WhatsApp está conectado"""
        try:
            response = requests.get(f'{self.whatsapp_url}/status', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('connected', False)
            return False
        except Exception as e:
            logger.warning(f'⚠️ Não foi possível verificar status do WhatsApp: {e}')
            return False

    def _get_target_groups(self) -> List[str]:
        """Obtém lista de grupos fixos ativos configurados para envio automático"""
        from . import database

        try:
            # Buscar grupos fixos ativos do banco de dados
            grupos_fixos = database.listar_grupos_fixos_ativos()

            if grupos_fixos:
                grupos_ids = [grupo['grupo_id'] for grupo in grupos_fixos]
                logger.info(f'📋 {len(grupos_ids)} grupos fixos ativos encontrados')
                return grupos_ids

            # Fallback: tentar variável de ambiente (para retrocompatibilidade)
            grupos_env = os.getenv('WHATSAPP_AUTO_SEND_GROUPS', '')
            if grupos_env:
                logger.warning('⚠️ Usando grupos do .env (fallback). Configure grupos fixos no sistema!')
                return [g.strip() for g in grupos_env.split(',') if g.strip()]

            logger.warning('⚠️ Nenhum grupo fixo ativo configurado')
            return []

        except Exception as e:
            logger.error(f'❌ Erro ao buscar grupos fixos: {e}')

            # Fallback em caso de erro
            grupos_env = os.getenv('WHATSAPP_AUTO_SEND_GROUPS', '')
            if grupos_env:
                return [g.strip() for g in grupos_env.split(',') if g.strip()]

            return []

    def _send_to_whatsapp(self, group_id: str, message: str, image_url: Optional[str] = None):
        """Envia mensagem para um grupo específico via WhatsApp Monitor"""
        try:
            payload = {
                'groupId': group_id,
                'message': message
            }

            if image_url:
                payload['imageUrl'] = image_url

            response = requests.post(
                f'{self.whatsapp_url}/groups/send-message',
                json=payload,
                timeout=30
            )

            # Verificar se há sessão ativa
            if response.status_code == 500:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                if error_data.get('error') == 'No sessions':
                    raise Exception('WhatsApp não está conectado. Escaneie o QR Code primeiro.')

            if response.status_code not in [200, 201]:
                raise Exception(f'Erro ao enviar: {response.status_code} - {response.text}')

            logger.info(f'[OK] Mensagem enviada com sucesso para {group_id}')

        except requests.exceptions.RequestException as e:
            logger.error(f'[ERRO] Erro de conexão com WhatsApp Monitor: {e}')
            raise Exception(f'WhatsApp Monitor não está acessível: {e}')
        except Exception as e:
            logger.error(f'[ERRO] Erro ao enviar para WhatsApp: {e}')
            raise

    def send_message_now(self, produto_id: str, grupos: List[str]) -> Dict:
        """Envia mensagem imediatamente (sem agendamento)"""
        from . import database

        try:
            # Buscar produto
            produto = database.obter_produto_db(produto_id)

            if not produto:
                return {'success': False, 'error': 'Produto não encontrado'}

            # Obter mensagem e imagem
            mensagem = produto.get('final_message', '')
            imagem_url = produto.get('processed_image_url') or produto.get('imagem_url')

            if not mensagem:
                return {'success': False, 'error': 'Produto sem mensagem formatada'}

            # Enviar para grupos
            resultados = []
            for grupo_id in grupos:
                try:
                    self._send_to_whatsapp(grupo_id, mensagem, imagem_url)
                    resultados.append({'grupo': grupo_id, 'sucesso': True})
                    time.sleep(2)  # Delay entre envios
                except Exception as e:
                    resultados.append({'grupo': grupo_id, 'sucesso': False, 'erro': str(e)})

            # Não marcar como enviado no banco (coluna não existe)
            # TODO: Adicionar coluna 'enviado_em' no Supabase se necessário

            return {
                'success': True,
                'resultados': resultados,
                'total_enviado': sum(1 for r in resultados if r['sucesso']),
                'total_falhou': sum(1 for r in resultados if not r['sucesso'])
            }

        except Exception as e:
            logger.error(f'❌ Erro ao enviar mensagem: {e}')
            return {'success': False, 'error': str(e)}


# Instância global do scheduler
message_scheduler = MessageScheduler()


# ============================================================================
# SCHEDULER PARA FILA DE MENSAGENS CLONADAS (ENVIO ESPAÇADO)
# ============================================================================

class CloneQueueScheduler:
    """
    Scheduler para processar fila de mensagens clonadas.
    Envia mensagens automaticamente quando chega o horário agendado.
    """

    def __init__(self):
        self.running = False
        self.thread = None
        self.check_interval = 30  # Verificar a cada 30 segundos
        self.whatsapp_url = os.getenv('WHATSAPP_MONITOR_URL', 'http://localhost:3001')
        self.timezone = pytz.timezone('America/Sao_Paulo')
        self.intervalo_minutos = 5  # Intervalo padrão entre envios

    def start(self):
        """Inicia o scheduler da fila de clonagem"""
        if self.running:
            logger.warning('[CLONE] Scheduler de clonagem ja esta rodando')
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info('[CLONE] Scheduler de fila de clonagem iniciado')

    def stop(self):
        """Para o scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info('[CLONE] Scheduler de fila de clonagem parado')

    def _load_config(self):
        """Carrega configuração do intervalo"""
        try:
            import json
            config_file = 'app/config/clone_queue_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.intervalo_minutos = config.get('intervalo_minutos', 5)
        except Exception:
            pass

    def _run(self):
        """Loop principal do scheduler"""
        logger.info('[CLONE] Scheduler rodando... Verificando fila a cada 30s')

        while self.running:
            try:
                self._load_config()
                self._process_queue()
            except Exception as e:
                logger.error(f'[CLONE] Erro no scheduler: {e}')
                import traceback
                logger.error(traceback.format_exc())

            time.sleep(self.check_interval)

    def _process_queue(self):
        """Processa mensagens pendentes na fila"""
        from . import database

        try:
            # Buscar próxima mensagem pendente que já passou do horário
            mensagem = database.obter_proxima_mensagem_fila()

            if not mensagem:
                return  # Nada para processar

            mensagem_id = mensagem['id']
            logger.info(f'[CLONE] Processando mensagem ID {mensagem_id}')

            # Marcar como "enviando"
            database.atualizar_status_mensagem_fila(mensagem_id, 'enviando')

            # Verificar conexão WhatsApp
            if not self._check_whatsapp_connection():
                database.atualizar_status_mensagem_fila(
                    mensagem_id, 'erro',
                    'WhatsApp nao conectado'
                )
                logger.warning('[CLONE] WhatsApp nao conectado. Mensagem ficara pendente.')
                return

            # Obter grupos destino
            grupos_destino = self._get_target_groups()

            if not grupos_destino:
                database.atualizar_status_mensagem_fila(
                    mensagem_id, 'erro',
                    'Nenhum grupo destino configurado'
                )
                logger.warning('[CLONE] Nenhum grupo destino configurado')
                return

            # Enviar mensagem
            texto = mensagem.get('mensagem_com_afiliado') or mensagem.get('mensagem_original', '')
            imagem_url = mensagem.get('imagem_url')

            sucesso_total = True
            for grupo_id in grupos_destino:
                try:
                    self._send_to_whatsapp(grupo_id, texto, imagem_url)
                    logger.info(f'[CLONE] Enviado para grupo: {grupo_id[:20]}...')
                    time.sleep(2)  # Delay entre grupos
                except Exception as e:
                    logger.error(f'[CLONE] Erro ao enviar para {grupo_id}: {e}')
                    sucesso_total = False

            # Atualizar status
            if sucesso_total:
                database.atualizar_status_mensagem_fila(mensagem_id, 'enviado')
                logger.info(f'[CLONE] Mensagem {mensagem_id} enviada com sucesso!')
            else:
                database.atualizar_status_mensagem_fila(
                    mensagem_id, 'erro',
                    'Falha em alguns grupos'
                )

        except Exception as e:
            logger.error(f'[CLONE] Erro ao processar fila: {e}')

    def _check_whatsapp_connection(self) -> bool:
        """Verifica se WhatsApp está conectado"""
        try:
            response = requests.get(f'{self.whatsapp_url}/status', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('connected', False)
            return False
        except Exception:
            return False

    def _get_target_groups(self) -> List[str]:
        """Obtém grupos destino ativos"""
        from . import database

        try:
            grupos_fixos = database.listar_grupos_fixos_ativos()
            if grupos_fixos:
                return [g['grupo_id'] for g in grupos_fixos]

            # Fallback: variável de ambiente
            grupos_env = os.getenv('WHATSAPP_AUTO_SEND_GROUPS', '')
            if grupos_env:
                return [g.strip() for g in grupos_env.split(',') if g.strip()]

            return []
        except Exception:
            return []

    def _send_to_whatsapp(self, group_id: str, message: str, image_url: Optional[str] = None):
        """Envia mensagem para grupo via WhatsApp Monitor"""
        try:
            payload = {
                'groupId': group_id,
                'message': message
            }

            if image_url and not image_url.startswith('data:'):
                payload['imageUrl'] = image_url

            response = requests.post(
                f'{self.whatsapp_url}/groups/send-message',
                json=payload,
                timeout=30
            )

            if response.status_code not in [200, 201]:
                raise Exception(f'HTTP {response.status_code}: {response.text}')

        except Exception as e:
            raise Exception(f'Erro ao enviar: {e}')

    def process_queue_now(self) -> Dict:
        """Processa fila imediatamente (chamado manualmente)"""
        from . import database

        try:
            mensagens_processadas = 0
            erros = 0

            while True:
                mensagem = database.obter_proxima_mensagem_fila()
                if not mensagem:
                    break

                mensagem_id = mensagem['id']

                try:
                    # Marcar como enviando
                    database.atualizar_status_mensagem_fila(mensagem_id, 'enviando')

                    # Verificar conexão
                    if not self._check_whatsapp_connection():
                        database.atualizar_status_mensagem_fila(mensagem_id, 'pendente')
                        return {
                            'success': False,
                            'error': 'WhatsApp nao conectado',
                            'processadas': mensagens_processadas
                        }

                    # Obter grupos
                    grupos = self._get_target_groups()
                    if not grupos:
                        database.atualizar_status_mensagem_fila(
                            mensagem_id, 'erro',
                            'Nenhum grupo configurado'
                        )
                        erros += 1
                        continue

                    # Enviar
                    texto = mensagem.get('mensagem_com_afiliado') or mensagem.get('mensagem_original', '')
                    imagem = mensagem.get('imagem_url')

                    for grupo in grupos:
                        self._send_to_whatsapp(grupo, texto, imagem)
                        time.sleep(1)

                    database.atualizar_status_mensagem_fila(mensagem_id, 'enviado')
                    mensagens_processadas += 1

                    # Delay entre mensagens
                    time.sleep(2)

                except Exception as e:
                    database.atualizar_status_mensagem_fila(mensagem_id, 'erro', str(e))
                    erros += 1

            return {
                'success': True,
                'processadas': mensagens_processadas,
                'erros': erros
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}


# Instância global do scheduler de clonagem
clone_queue_scheduler = CloneQueueScheduler()
