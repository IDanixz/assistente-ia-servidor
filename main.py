import os

from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    timeout=60.0
)


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

        resposta = client.responses.create(
            model="gpt-4.1-mini",
            input=pergunta
        )

        print("Resposta recebida da IA")

        return jsonify({
            "resposta": resposta.output_text
        })

    except Exception as e:

        print(f"ERRO OPENAI: {type(e).__name__}: {str(e)}")

        return jsonify({
            "erro": str(e),
            "tipo": type(e).__name__
        }), 500


if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
