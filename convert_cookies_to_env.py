#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para converter cookies exportados do navegador (JSON) para formato .env
"""

import json
import sys

def convert_cookies_json_to_env(json_file_path):
    """
    Converte arquivo JSON de cookies para formato .env
    """
    print("=" * 80)
    print("🔄 CONVERSOR DE COOKIES JSON PARA .ENV")
    print("=" * 80)
    print()

    try:
        # Ler arquivo JSON
        print(f"📂 Lendo arquivo: {json_file_path}")
        with open(json_file_path, 'r', encoding='utf-8') as f:
            cookies = json.load(f)

        print(f"✅ Arquivo lido com sucesso! ({len(cookies)} cookies encontrados)")
        print()

        # Cookies importantes que precisamos
        important_cookies = {
            '_csrf': 'ML_COOKIE__CSRF',
            'orgnickp': 'ML_COOKIE_ORGNICKP',
            'orguseridp': 'ML_COOKIE_ORGUSERIDP',
            'orguserid': 'ML_COOKIE_ORGUSERID',
            '_mldataSessionId': 'ML_COOKIE__MLDATASESSIONID',
            '_d2id': 'ML_COOKIE__D2ID',
            'ssid': 'ML_COOKIE_SSID',
            'ftid': 'ML_COOKIE_FTID',
            'nsa_rotok': 'ML_COOKIE_NSA_ROTOK',
            'x-meli-session-id': 'ML_COOKIE_X_MELI_SESSION_ID',
            'cp': 'ML_COOKIE_CP'
        }

        # Encontrar CSRF token
        csrf_token = None

        # Extrair cookies
        env_lines = []
        env_lines.append("# ============================================================================")
        env_lines.append("# CONFIGURAÇÃO DO MERCADO LIVRE - COPIE ESTAS LINHAS PARA SEU ARQUIVO .env")
        env_lines.append("# ============================================================================")
        env_lines.append("")
        env_lines.append("# ID de afiliado (seu nickname no ML)")
        env_lines.append("MERCADOLIVRE_AFFILIATE_ID=gabrielvilelaluiz")
        env_lines.append("")

        print("🔍 Extraindo cookies importantes...")
        print()

        found_cookies = {}

        for cookie in cookies:
            cookie_name = cookie.get('name', '')
            cookie_value = cookie.get('value', '')

            # Verificar se é um cookie importante
            if cookie_name in important_cookies:
                env_var_name = important_cookies[cookie_name]
                found_cookies[cookie_name] = cookie_value

                # CSRF token é especial
                if cookie_name == '_csrf':
                    csrf_token = cookie_value

                print(f"  ✓ {cookie_name:<25} → {env_var_name}")

        print()

        # Adicionar CSRF token
        if csrf_token:
            env_lines.append("# CSRF Token (essencial para requisições POST)")
            env_lines.append(f"ML_CSRF_TOKEN={csrf_token}")
            env_lines.append("")
            print(f"✅ CSRF Token encontrado: {csrf_token[:30]}...")
        else:
            print("⚠️  CSRF Token NÃO encontrado!")
            env_lines.append("# CSRF Token (NÃO ENCONTRADO - você precisa obter manualmente)")
            env_lines.append("ML_CSRF_TOKEN=")
            env_lines.append("")

        print()

        # Adicionar cookies
        env_lines.append("# Cookies de sessão")
        for cookie_name, env_var_name in important_cookies.items():
            if cookie_name in found_cookies:
                env_lines.append(f"{env_var_name}={found_cookies[cookie_name]}")

        env_lines.append("")
        env_lines.append("# ============================================================================")
        env_lines.append("# INSTRUÇÕES:")
        env_lines.append("# 1. Abra seu arquivo .env na raiz do projeto")
        env_lines.append("# 2. Copie TODAS as linhas acima")
        env_lines.append("# 3. Cole no seu arquivo .env")
        env_lines.append("# 4. Salve o arquivo")
        env_lines.append("# 5. Reinicie o servidor Flask")
        env_lines.append("# 6. Execute: python test_ml_affiliate.py")
        env_lines.append("# ============================================================================")

        # Salvar arquivo .env.ML_CONFIG
        output_file = '.env.ML_CONFIG'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(env_lines))

        print()
        print("─" * 80)
        print()
        print(f"✅ Arquivo gerado com sucesso: {output_file}")
        print()
        print("📋 Estatísticas:")
        print(f"   - Total de cookies no JSON: {len(cookies)}")
        print(f"   - Cookies importantes encontrados: {len(found_cookies)}/{len(important_cookies)}")
        print(f"   - CSRF Token: {'✅ Encontrado' if csrf_token else '❌ NÃO encontrado'}")
        print()

        # Mostrar cookies faltando
        missing_cookies = [name for name in important_cookies.keys() if name not in found_cookies]
        if missing_cookies:
            print("⚠️  Cookies importantes que NÃO foram encontrados:")
            for cookie_name in missing_cookies:
                print(f"   - {cookie_name}")
            print()

        print("─" * 80)
        print()
        print("📝 PRÓXIMOS PASSOS:")
        print()
        print("1. Abra o arquivo .env.ML_CONFIG que foi gerado")
        print("2. Copie TODO o conteúdo")
        print("3. Cole no seu arquivo .env (na raiz do projeto)")
        print("4. Salve o arquivo .env")
        print("5. Reinicie o servidor Flask")
        print("6. Execute: python test_ml_affiliate.py")
        print()
        print("=" * 80)

    except FileNotFoundError:
        print(f"❌ Erro: Arquivo não encontrado: {json_file_path}")
        print()
        print("💡 Certifique-se de que:")
        print("   1. O arquivo existe no caminho especificado")
        print("   2. O caminho está correto")
        print()
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao ler JSON: {e}")
        print()
        print("💡 O arquivo não é um JSON válido.")
        print()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    # Caminho padrão do arquivo
    default_path = r'C:\Users\Joao_\Downloads\download.json'

    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = default_path

    convert_cookies_json_to_env(json_file)
