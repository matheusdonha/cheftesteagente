from flask import request, jsonify
import sys
from app import app
import os
import string
from app.utils.supabase_client import upload_file_to_supabase, SUPABASE_LIBRARY_URL
from app.agent_logic import gerar_resposta
from app.utils.helpers import inserir_mensagem, get_file_url_telegram, download_file,enviar_mensagem_telegram, buscar_historico, deletar_historico, transcrever_audio

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_BUCKET_NAME = "chat-media"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data['message']['chat']['id']
        if "text" in data["message"]:
            mensagem = data['message'].get('text', '')
            print(f"Chat ID: {chat_id}, Texto: {mensagem}", file=sys.stderr)
            try:
                inserir_mensagem(str(chat_id), "user", mensagem)
                historico = buscar_historico(str(chat_id))
                print(f"Histórico enviado para OpenAI: {historico}", file=sys.stderr)
                resposta = gerar_resposta(historico)
                inserir_mensagem(str(chat_id), "assistant", resposta)
                print("Resposta gerada:", resposta, file=sys.stderr)
                enviar_mensagem_telegram(chat_id, resposta)

            except Exception as e:
                print("Erro no processamento:", e, file=sys.stderr)

        elif "photo" in data["message"]:
            photo = data['message']['photo'][-1]
            file_id = photo['file_id']
            caption = data['message'].get('caption', '')
            print(f"Chat ID: {chat_id}, Foto File ID: {file_id}, Legenda: '{caption}'", file=sys.stderr)

            temp_file_path = None  # Inicializa para garantir que exista
            try:
                # Obter URL do TELEGRAM
                image_url_telegram = get_file_url_telegram(file_id)
                if image_url_telegram:
                    # 2. Baixar o arquivo
                    temp_file_path = f"/tmp/{file_id}.jpg"
                    download_file(image_url_telegram, temp_file_path)

                    # 3. Upload para Supabase
                    supabase_file_name = f"telegram_photos/{file_id}.jpg"
                    # Chama a função de upload que agora retorna True/False
                    upload_success = upload_file_to_supabase(temp_file_path, SUPABASE_BUCKET_NAME, supabase_file_name)

                    if upload_success:
                        # CONSTRÓI A URL PÚBLICA MANUALMENTE AQUI
                        # Substitua 'SUPABASE_URL' pela sua variável que contém 'https://ohwzezjffhjhetzsnjdd.supabase.co'
                        supabase_public_url = f"{SUPABASE_LIBRARY_URL}/storage/v1/object/public/{SUPABASE_BUCKET_NAME}/{supabase_file_name}"

                        content = []
                        if caption:
                            content.append({"type": "text", "text": caption})
                        content.append(
                            {"type": "image_url", "image_url": {"url": supabase_public_url}})  # Usa a URL construída

                        # 5. Inserir mensagem com conteúdo multimodal
                        inserir_mensagem(str(chat_id), "user", content)

                        # 6. Buscar histórico e gerar resposta
                        historico = buscar_historico(str(chat_id))
                        print(f"Histórico enviado para OpenAI: {historico}", file=sys.stderr)
                        resposta = gerar_resposta(historico)

                        # 7. Inserir resposta do assistente e enviar
                        inserir_mensagem(str(chat_id), "assistant", resposta)
                        enviar_mensagem_telegram(chat_id, resposta)
                    else:
                        enviar_mensagem_telegram(chat_id, "Desculpe, não consegui armazenar a imagem.")
                else:
                    enviar_mensagem_telegram(chat_id, "Desculpe, não consegui obter a imagem do Telegram.")
            except Exception as e:
                print(f"Erro no processamento de foto: {e}", file=sys.stderr)
                enviar_mensagem_telegram(chat_id, "Desculpe, ocorreu um erro ao processar a foto.")
            finally:
                # 8. Limpar arquivo temporário, garantindo que seja removido
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        elif "audio" in data["message"]:
            audio = data['message']['audio']
            file_id = audio['file_id']
            print(f"Chat ID: {chat_id}, Audio: {file_id}", file=sys.stderr)
            temp_file_path = None  # Inicializa a variável para garantir que exista
            try:
                # 1. Obter a URL do Telegram
                audio_url_telegram = get_file_url_telegram(file_id)
                if audio_url_telegram:
                    # 2. Baixar o arquivo (vamos usar .ogg, que é comum para voz)
                    print ("Url de áudio temporário do telegram foi pega")
                    temp_file_path = f"/tmp/{file_id}.ogg"
                    download_file(audio_url_telegram, temp_file_path)
                    print("Url de áudio temporário do telegram foi baixada")
                    # 3. Transcrever o áudio
                    transcribed_text = transcrever_audio(temp_file_path)
                    print("Url de áudio temporário do telegram foi trancrita")
                    # 4. Inserir a mensagem transcrita no histórico (como texto)
                    inserir_mensagem(str(chat_id), "user", transcribed_text)
                    print("Transcrição foi inserida no histórico")
                    # 5. Gerar a resposta do agente
                    historico = buscar_historico(str(chat_id))
                    print(f"Histórico enviado para OpenAI: {historico}", file=sys.stderr)
                    resposta = gerar_resposta(historico)
                    # 6. Inserir a resposta do assistente e enviar
                    inserir_mensagem(str(chat_id), "assistant", resposta)
                    enviar_mensagem_telegram(chat_id, resposta)
                else:
                    enviar_mensagem_telegram(chat_id, "Desculpe, não consegui obter seu áudio do Telegram.")
            except Exception as e:
                print(f"Erro no processamento de áudio: {e}", file=sys.stderr)
                enviar_mensagem_telegram(chat_id, "Desculpe, ocorreu um erro ao processar seu áudio.")
            finally:
                # 7. Limpar arquivo temporário, garantindo que seja removido mesmo em caso de erro
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        elif "video" in data["message"]:
            video_file_id = data['message']['video']['file_id']
            caption = data['message'].get('caption', '')
            print(
                f"Chat ID: {chat_id}, Vídeo File ID: {video_file_id}, Legenda: '{caption}' (sem suporte para processamento)",
                file=sys.stderr)

            # Envia uma mensagem amigável de volta ao usuário
            enviar_mensagem_telegram(chat_id,
                                     "Desculpe, ainda não consigo processar vídeos. Por favor, envie uma foto, um áudio ou um texto.")

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




