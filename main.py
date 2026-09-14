import os

from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)


@app.route("/")
def home():
    return "Servidor da Assistente IA funcionando!"


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    pergunta = data.get("pergunta", "")

    if not pergunta:
        return jsonify({
            "erro": "Pergunta vazia"
        }), 400

    try:

        resposta = client.responses.create(
            model="gpt-4.1-mini",
            input=pergunta
        )

        return jsonify({
            "resposta": resposta.output_text
        })

    except Exception as e:

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
