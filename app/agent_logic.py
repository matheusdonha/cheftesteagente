from openai import OpenAI
from config import OPENAI_API_KEY
import sys

client = OpenAI(api_key=OPENAI_API_KEY)

def gerar_resposta(historico):
    if not historico:
        historico = []
    try:
        mensagens = [{"role": "system", "content": """
                                       Você é um chef de cozinha virtual especializado em receitas internacionais. 
                                       Seu papel é ajudar os usuários a criarem receitas incríveis com o que têm em casa, sugerir substituições de ingredientes, explicar técnicas culinárias e dar dicas de preparo. 
                                       Você deve ser simpático, encorajador e prático, falando como um chef experiente que quer que todos se sintam confiantes na cozinha.
    
                                       Características:
                                       - Fala de forma leve e acessível
                                       - Explica técnicas de modo didático
                                       - Faz perguntas para entender o que o usuário tem em casa
                                       - Sempre sugere receitas ou variações práticas
                                       -Considere o histórico da conversa
                                               """}] + historico
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=mensagens
        )
        return resposta.choices[0].message.content
    except Exception as e:
        print(f"ERRO ao gerar resposta do agente: {e}", file=sys.stderr)
        return f"Desculpe, estou com dificuldades técnicas. Tente novamente em alguns minutos."




