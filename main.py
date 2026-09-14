import os
import requests

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

        pergunta = data.get("pergunta", "")

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
                        "content": "Você é uma assistente de voz amigável chamada Assistente IA. Responda em português do Brasil, de forma curta e natural."
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
                "erro": "Erro na IA"
            }), 500

        resultado = resposta.json()

        texto = resultado["choices"][0]["message"]["content"]

        print("Resposta:", texto)

        return jsonify({
            "resposta": texto
        })

    except Exception as e:

        print("ERRO:", str(e))

        return jsonify({
            "erro": str(e)
        }), 500


if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
