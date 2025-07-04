from flask import request, jsonify
import sys
from app import app
from app.agent_logic import gerar_resposta
from app.utils.helpers import inserir_mensagem,enviar_mensagem_telegram, buscar_historico, deletar_historico


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data['message']['chat']['id']
        mensagem = data['message'].get('text', '')

        print(f"Chat ID: {chat_id}, Texto: {mensagem}", file=sys.stderr)

        try:
            inserir_mensagem(chat_id, "user", mensagem)
            historico = buscar_historico(chat_id)
            resposta = gerar_resposta(historico)
            inserir_mensagem(chat_id, "assistant", resposta)

            print("Resposta gerada:", resposta, file=sys.stderr)
            enviar_mensagem_telegram(chat_id, resposta)

        except Exception as e:
            print("Erro no processamento:", e, file=sys.stderr)

    return jsonify({"status": "ok"}), 200




@app.route('/responder', methods=['POST'])
def responder():
    data = request.get_json()
    mensagem = data.get("mensagem")
    user_id = data.get("user_id")

    if not user_id or not mensagem:
        return jsonify({"erro": "Campos 'user_id' e 'mensagem' são obrigatórios"}), 400

    try:
        inserir_mensagem(user_id, "user",  mensagem)
        historico=buscar_historico(user_id)
        resposta = gerar_resposta(historico)


        inserir_mensagem(user_id, "assistant", resposta)
        return jsonify({"resposta": resposta})
    except Exception as erro:
        return jsonify({"erro": str(erro)}), 500


@app.route('/historico', methods=['GET'])
def historico():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify("user_id obrigatório"), 400
    try:
        historico = buscar_historico(user_id)
        if not historico:
            return jsonify("Sem histórico"), 400
        return jsonify({"historico": historico})
    except Exception as erro:
        return jsonify({'erro': str(erro)}), 500


@app.route('/delete', methods=['DELETE'])
def delete():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify("user_id obrigatório"), 400
    try:
        deletar_historico(user_id)
        return jsonify({"resposta": "Histórico apagado com sucesso"})
    except Exception as erro:
        return jsonify({'erro': str(erro)}), 500




