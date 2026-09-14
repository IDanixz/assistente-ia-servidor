import os
import requests
import re

from flask import Flask, request, jsonify

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")


@app.route("/")
def home():
    return "Servidor da Assistente IA funcionando!"


@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "erro": "Nenhum dado recebido"
            }), 400

        pergunta = data.get("pergunta", "")

        if not pergunta:
            return jsonify({
                "erro": "Pergunta vazia"
            }), 400

        print(f"Pergunta recebida: {pergunta}")

        resposta = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openrouter/free",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Você é uma assistente de voz amigável chamada "
                            "Assistente IA. Responda sempre em português do "
                            "Brasil, de forma curta, natural e clara."
                        )
                    },
                    {
                        "role": "user",
                        "content": pergunta
                    }
                ]
            },
            timeout=30
        )

        print("Status da IA:", resposta.status_code)

        if resposta.status_code != 200:

            print("ERRO OPENROUTER:", resposta.text)

            return jsonify({
                "erro": "Erro ao conectar com a IA"
            }), 500


        resultado = resposta.json()

        texto = resultado["choices"][0]["message"]["content"]


        # Corrige caracteres escapados
        # Exemplo: ent\u00e3o -> então
        def corrigir_unicode(texto):

            return re.sub(
                r'\\u([0-9a-fA-F]{4})',
                lambda x: chr(int(x.group(1), 16)),
                texto
            )


        texto = corrigir_unicode(texto)


        print("Resposta:", texto)


        return jsonify(
            {
                "resposta": texto
            },
            ensure_ascii=False
        )


    except Exception as e:

        print("ERRO:", str(e))

        return jsonify(
            {
                "erro": str(e)
            },
            ensure_ascii=False
        ), 500


if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
