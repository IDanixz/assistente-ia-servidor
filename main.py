import os

from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
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

        resposta = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=pergunta
        )

        texto = resposta.text

        print("Resposta recebida da Gemini")

        return jsonify({
            "resposta": texto
        })

    except Exception as e:

        print(
            f"ERRO GEMINI: "
            f"{type(e).__name__}: {str(e)}"
        )

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
