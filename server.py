# server.py - Servidor Flask para integração com Shopee
from flask import Flask, request, jsonify
import os
import hashlib
import hmac
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Importa a lógica principal do seu bot
# Certifique-se de que seu bot_v14.py foi renomeado para bot_logic.py
from bot_logic import assistente_virtual_bot, ATENDIMENTO_HUMANO_ATIVO, CONVERSA_ENCAMINHADA_HUMANO, get_resposta_regra

app = Flask(__name__)

# Credenciais da Shopee carregadas do .env
PARTNER_ID = int(os.getenv('SHOPEE_PARTNER_ID'))
API_KEY = os.getenv('SHOPEE_API_KEY')
API_SECRET = os.getenv('SHOPEE_API_SECRET').encode('utf-8') # A chave secreta deve ser bytes
SHOP_ID = int(os.getenv('SHOPEE_SHOP_ID'))
BASE_URL = "https://open.shopee.com" # URL base da API da Shopee

# Dicionário para armazenar tokens de acesso e refresh_token por shop_id
# Em um ambiente de produção, isso seria armazenado em um banco de dados
# ou cache persistente.
SHOP_TOKENS = {} # Ex: {shop_id: {'access_token': '...', 'refresh_token': '...', 'expire_time': datetime}}

def generate_shopee_signature(url_path, access_token, shop_id, partner_id, timestamp, secret_key):
    """Gera a assinatura HMAC-SHA256 para requisições da Shopee API."""
    base_string = f"{url_path}|{access_token}|{shop_id}|{partner_id}|{timestamp}"
    h = hmac.new(secret_key, base_string.encode('utf-8'), hashlib.sha256)
    return h.hexdigest()

def get_access_token(shop_id):
    """
    Função mock para obter o access_token.
    Em produção, você precisaria implementar o fluxo OAuth 2.0 completo
    para obter e renovar o access_token.
    """
    # TODO: Implementar a lógica real de OAuth 2.0 para obter e renovar o access_token
    # Por enquanto, estamos usando um placeholder.
    # Você precisará de um access_token válido para fazer chamadas reais à API.
    print(f"⚠️ ATENÇÃO: Usando access_token placeholder para shop_id {shop_id}. "
          "Implemente o fluxo OAuth 2.0 para obter um token real.")
    return "SEU_ACCESS_TOKEN_REAL_AQUI" # Substitua por um token real obtido via OAuth

def reply_shopee_message(shop_id, conversation_id, message_content):
    """Envia uma resposta para a Shopee API."""
    url_path = "/api/v2/message/reply_message"
    timestamp = int(datetime.now().timestamp())
    access_token = get_access_token(shop_id) # Obtenha o token real

    if not access_token or access_token == "SEU_ACCESS_TOKEN_REAL_AQUI":
        print("❌ Erro: access_token inválido. Não é possível responder à mensagem.")
        return False

    signature = generate_shopee_signature(url_path, access_token, shop_id, PARTNER_ID, timestamp, API_SECRET)

    headers = {
        "Content-Type": "application/json",
        "Host": "open.shopee.com",
        "x-shopee-api-partner-id": str(PARTNER_ID),
        "x-shopee-api-timestamp": str(timestamp),
        "x-shopee-api-access-token": access_token,
        "x-shopee-api-shop-id": str(shop_id),
        "x-shopee-api-signature": signature
    }

    payload = {
        "conversation_id": conversation_id,
        "message_type": "TEXT",
        "content": {
            "text": message_content
        }
    }

    try:
        response = requests.post(f"{BASE_URL}{url_path}", headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Levanta um erro para códigos de status HTTP ruins (4xx ou 5xx)
        print(f"✅ Resposta enviada para Shopee: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar resposta para Shopee: {e}")
        print(f"Resposta da Shopee: {response.text if 'response' in locals() else 'N/A'}")
        return False

def mark_shopee_message_unread(shop_id, conversation_id):
    """Marca uma conversa como não lida na Shopee API."""
    url_path = "/api/v2/message/mark_message_unread"
    timestamp = int(datetime.now().timestamp())
    access_token = get_access_token(shop_id) # Obtenha o token real

    if not access_token or access_token == "SEU_ACCESS_TOKEN_REAL_AQUI":
        print("❌ Erro: access_token inválido. Não é possível marcar mensagem como não lida.")
        return False

    signature = generate_shopee_signature(url_path, access_token, shop_id, PARTNER_ID, timestamp, API_SECRET)

    headers = {
        "Content-Type": "application/json",
        "Host": "open.shopee.com",
        "x-shopee-api-partner-id": str(PARTNER_ID),
        "x-shopee-api-timestamp": str(timestamp),
        "x-shopee-api-access-token": access_token,
        "x-shopee-api-shop-id": str(shop_id),
        "x-shopee-api-signature": signature
    }

    payload = {
        "conversation_id": conversation_id
    }

    try:
        response = requests.post(f"{BASE_URL}{url_path}", headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"✅ Conversa {conversation_id} marcada como não lida na Shopee: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao marcar conversa como não lida na Shopee: {e}")
        print(f"Resposta da Shopee: {response.text if 'response' in locals() else 'N/A'}")
        return False

@app.route('/shopee/webhook', methods=['POST'])
def shopee_webhook():
    """Endpoint para receber webhooks de mensagens da Shopee."""
    data = request.json
    print(f"Webhook da Shopee recebido: {json.dumps(data, indent=2)}")

    # Verifica a assinatura do webhook para garantir que é da Shopee
    # TODO: Implementar verificação de assinatura do webhook (requer o secret key do webhook)
    # Por simplicidade, estamos pulando a verificação de assinatura aqui, mas é CRÍTICO para segurança em produção.

    # Extrai informações da mensagem
    # A estrutura do webhook pode variar, consulte a documentação da Shopee Open Platform v2
    try:
        # Exemplo de como extrair dados, ajuste conforme a documentação da Shopee
        shop_id = data.get('shop_id')
        message_data = data.get('data', {}).get('message')
        conversation_id = message_data.get('conversation_id')
        sender_id = message_data.get('from_user_id') # ID do cliente
        message_content = message_data.get('content', {}).get('text', '') # Conteúdo da mensagem do cliente

        if not all([shop_id, conversation_id, sender_id, message_content is not None]):
            print("❌ Dados essenciais da mensagem ausentes no webhook.")
            return jsonify({"message": "Dados da mensagem incompletos"}), 400

        print(f"Mensagem do cliente ({sender_id}) na conversa {conversation_id} da loja {shop_id}: {message_content}")

        # Simula o ID da sessão do bot com o conversation_id da Shopee
        sessao_id = str(conversation_id)

        # Verifica se a conversa foi encaminhada para atendimento humano
        if CONVERSA_ENCAMINHADA_HUMANO.get(sessao_id, False):
            # Se já foi encaminhada, a Jessica não responde mais, apenas marca como não lida
            print(f"Conversa {sessao_id} já encaminhada para humano. Marcando como não lida.")
            mark_shopee_message_unread(shop_id, conversation_id)
            return jsonify({"message": "Conversa já encaminhada para humano, marcada como não lida."}), 200

        # Processa a mensagem com a lógica do seu bot
        resposta_bot = assistente_virtual_bot(sessao_id, message_content)
        print(f"Resposta do bot para {sessao_id}: {resposta_bot}")

        # Envia a resposta de volta para a Shopee
        reply_shopee_message(shop_id, conversation_id, resposta_bot)

        # Verifica se a resposta do bot indica transferência para humano
        # A frase "atendente humano vai assumir" é usada como gatilho
        if "atendente humano vai assumir" in resposta_bot.lower() and \
           "Vou deixar seu elogio registrado e encaminhar para que um atendente humano possa te responder pessoalmente" not in resposta_bot:
            print(f"Bot indicou transferência para humano na sessão {sessao_id}. Marcando como não lida.")
            CONVERSA_ENCAMINHADA_HUMANO[sessao_id] = True # Marca a sessão como transferida
            mark_shopee_message_unread(shop_id, conversation_id) # Marca a conversa como não lida

        return jsonify({"message": "Mensagem processada com sucesso"}), 200

    except Exception as e:
        print(f"❌ Erro ao processar webhook da Shopee: {e}")
        return jsonify({"message": "Erro interno do servidor"}), 500

@app.route('/oauth/callback', methods=['GET'])
def oauth_callback():
    """Endpoint para o callback OAuth da Shopee."""
    # Este endpoint é onde a Shopee redirecionará após o vendedor autorizar seu app.
    # Você precisará extrair o 'code' e o 'shop_id' dos parâmetros da URL
    # e usá-los para trocar por um access_token e refresh_token.
    code = request.args.get('code')
    shop_id = request.args.get('shop_id')
    print(f"OAuth Callback recebido: code={code}, shop_id={shop_id}")

    if code and shop_id:
        # TODO: Implementar a troca do 'code' por 'access_token' e 'refresh_token'
        # e armazená-los de forma persistente (ex: em SHOP_TOKENS ou DB).
        # Este é um passo CRÍTICO para a autenticação real.
        print("⚠️ ATENÇÃO: Implemente a troca de código OAuth por tokens reais aqui.")
        return jsonify({"message": "OAuth callback recebido. Implemente a troca de código por tokens."}), 200
    else:
        return jsonify({"message": "Parâmetros OAuth incompletos."}), 400

if __name__ == '__main__':
    # Use as variáveis de ambiente para host e porta
    host = os.getenv('BOT_HOST', '0.0.0.0')
    port = int(os.getenv('BOT_PORT', 8000))
    print(f"🚀 Servidor Flask iniciado em http://{host}:{port}")
    app.run(host=host, port=port, debug=True) # debug=True para desenvolvimento, False para produção
