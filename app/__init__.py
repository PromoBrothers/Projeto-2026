# /mercado_livre_scraper/app/__init__.py

import sys
import os
from flask import Flask
from datetime import timedelta

# Configura a codificação de E/S para UTF-8
if sys.version_info.major == 3:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def create_app():
    """Cria e configura a instância da aplicação Flask."""
    app = Flask(__name__)

    # Configurações de segurança e sessão
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'promo-brothers-secret-key-2024-ultra-secure')
    app.config['SESSION_COOKIE_SECURE'] = False  # True apenas em HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Sessão dura 7 dias

    # Registra as rotas (Blueprints)
    from . import routes
    app.register_blueprint(routes.main_bp)

    # Iniciar scheduler de mensagens automáticas
    from .scheduler import message_scheduler, clone_queue_scheduler
    message_scheduler.start()
    clone_queue_scheduler.start()
    print('✅ Scheduler de mensagens iniciado', file=sys.stderr)
    print('✅ Scheduler de fila de clonagem iniciado', file=sys.stderr)

    return app