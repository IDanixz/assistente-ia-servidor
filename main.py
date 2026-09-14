from flask import Flask, request, jsonify
import requests
import os
import time
import logging
from collections import defaultdict, deque
from threading import Lock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
API_KEY = os.environ.get("APP_API_KEY")  # chave própria do app, separada da do OpenRouter

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Se o primeiro modelo falhar (erro/indisponível), tenta o próximo da lista.
MODELOS = [
    "openrouter/free",
    "meta-llama/llama-3.1-8b-instruct:free",
]

MAX_PERGUNTA_CHARS = 1000
MAX_HISTORICO_ITENS = 10

# Rate limiting simples em memória: no máximo N requisições por IP a cada janela de tempo.
RATE_LIMIT_MAX_REQUISICOES = 10
RATE_LIMIT_JANELA_SEGUNDOS = 60
_requisicoes_por_ip = defaultdict(deque)
_rate_limit_lock = Lock()


def _rate_limit_excedido(ip: str) -> bool:
    agora = time.time()
    with _rate_limit_lock:
        fila = _requisicoes_por_ip[ip]

        while fila and agora - fila[0] > RATE_LIMIT_JANELA_SEGUNDOS:
            fila.popleft()

        if len(fila) >= RATE_LIMIT_MAX_REQUISICOES:
            return True

        fila.append(agora)
        return False

SYSTEM_PROMPT = """
Você é uma assistente de voz amigável chamada Assistente IA.

Responda sempre em português do Brasil.

Use o histórico da conversa para entender referências como:
"ele", "ela", "isso", "aquilo", "essa pessoa", etc.

Responda de forma natural, curta e clara, porque sua resposta será falada em voz alta.

Não diga que você não sabe o assunto se ele estiver no histórico da conversa.
"""


@app.route("/")
def inicio():
    return "Assistente IA online!"


@app.before_request
def verificar_api_key():
    # Só protege a rota /chat; a raiz "/" continua livre para health check
    if request.path == "/chat":
        chave_enviada = request.headers.get("X-API-Key")
        if not API_KEY or chave_enviada != API_KEY:
            logger.warning("Tentativa de acesso não autorizado a /chat")
            return jsonify({"erro": "Não autorizado"}), 401

        ip_cliente = request.headers.get("X-Forwarded-For", request.remote_addr)
        if _rate_limit_excedido(ip_cliente):
            logger.warning(f"Rate limit excedido para {ip_cliente}")
            return jsonify({"erro": "Muitas requisições, tente novamente em instantes"}), 429


@app.route("/chat", methods=["POST"])
def chat():
    try:
        dados = request.get_json(silent=True)

        if not dados:
            return jsonify({"erro": "Corpo da requisição inválido"}), 400

        pergunta = str(dados.get("pergunta", "")).strip()
        historico = dados.get("historico", [])

        if not pergunta:
            return jsonify({"erro": "Pergunta vazia"}), 400

        if len(pergunta) > MAX_PERGUNTA_CHARS:
            return jsonify({
                "erro": f"Pergunta muito longa (máximo {MAX_PERGUNTA_CHARS} caracteres)"
            }), 400

        if not isinstance(historico, list):
            historico = []

        mensagens = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        historico = historico[-MAX_HISTORICO_ITENS:]

        for mensagem in historico:
            if not isinstance(mensagem, dict):
                continue

            role = mensagem.get("role")
            content = mensagem.get("content")

            if role in ["user", "assistant"] and content:
                mensagens.append({
                    "role": role,
                    "content": str(content)[:MAX_PERGUNTA_CHARS]
                })

        mensagens.append({
            "role": "user",
            "content": pergunta
        })

        ultimo_erro = None

        for modelo in MODELOS:
            try:
                resposta = requests.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": modelo,
                        "messages": mensagens,
                        "temperature": 0.7,
                        "max_tokens": 300
                    },
                    timeout=45
                )

                if resposta.status_code == 200:
                    dados_resposta = resposta.json()
                    texto = dados_resposta["choices"][0]["message"]["content"]
                    return jsonify({"resposta": texto})

                logger.warning(
                    f"Modelo {modelo} falhou ({resposta.status_code}): {resposta.text}"
                )
                ultimo_erro = f"{resposta.status_code}: {resposta.text}"

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout no modelo {modelo}")
                ultimo_erro = "timeout"
                continue

        logger.error(f"Todos os modelos falharam. Último erro: {ultimo_erro}")
        return jsonify({
            "erro": "Todos os modelos de IA falharam, tente novamente mais tarde"
        }), 502

    except requests.exceptions.Timeout:
        logger.error("Timeout ao chamar OpenRouter")
        return jsonify({
            "erro": "A IA demorou muito para responder."
        }), 504

    except Exception as e:
        logger.exception("Erro inesperado em /chat")
        return jsonify({
            "erro": "Erro interno no servidor"
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port
    )
