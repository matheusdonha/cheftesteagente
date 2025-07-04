import psycopg2
import os
import requests
from psycopg2 import pool
from dotenv import load_dotenv
from urllib.parse import urlparse, quote_plus # Importe urlparse e quote_plus

load_dotenv()  # Carrega variáveis de ambiente uma vez no início


DB_PASSWORD = os.environ['SUPABASE_PASSWORD']


# Cria o pool de conexões
# minconn: Número mínimo de conexões ociosas no pool
# maxconn: Número máximo de conexões que o pool pode ter
# O pool é global para ser acessível por todas as funções.
# Adicionamos um try-except para a inicialização do pool, pois ela é crítica.

try:
    connection_pool= pool.SimpleConnectionPool(minconn=1, maxconn=10, dsn=f"host=db.ohwzezjffhjhetzsnjdd.supabase.co port=5432 dbname=postgres user=postgres password={DB_PASSWORD}")
    print("Connection pool established")
except Exception as e:
    print(f"ERRO: Não foi possível criar o pool de conexões do Supabase. Verifique a SUPABASE_URL. Erro: {e}")
    # Se o pool não puder ser inicializado, a aplicação não deve continuar.
    exit(1)

# --- Funções Auxiliares para o Pool ---

def get_db_connection():
    """Obtém uma conexão do pool."""
    # Retorna uma conexão do pool. Erros na obtenção serão propagados.
    try:
        return connection_pool.getconn()
    except Exception as e:
        print(f"ERRO: Falha ao obter conexão do pool. Erro: {e}")
        raise  # Re-lança a exceção para ser tratada pela função chamadora

def put_db_connection(con):
    """Devolve uma conexão ao pool."""
    if con: # Garante que a conexão existe antes de tentar devolvê-la
        try:
            connection_pool.putconn(con)
        except Exception as e:
            print(f"AVISO: Falha ao devolver conexão ao pool. Erro: {e}")
            # Este é um erro menos crítico, apenas logamos. A conexão pode ser perdida.


def enviar_mensagem_telegram(chat_id, texto):
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("ERRO: TELEGRAM_TOKEN não configurado nas variáveis de ambiente.")
        raise ValueError("Token do Telegram não configurado.")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id":chat_id , "text":texto}

    try:
        response=requests.post(url, json=payload)
        response.raise_for_status()  # Lança um erro para status HTTP 4xx/5xx
        print(f"Mensagem enviada para {chat_id} com sucesso.")

    except requests.exceptions.RequestException as e:
        print(f"ERRO: Falha ao enviar mensagem ao Telegram para {chat_id}. Erro: {e}")
        raise  # Re-lança a exceção para ser tratada nas rotas


def inserir_mensagem(user_id, role, message_content):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""INSERT INTO tabelademensagens(user_id, role, messages) VALUES (%s, %s, %s)""",
                    (user_id, role, message_content))
        conn.commit()
        print(f"Mensagem inserida para user_id: {user_id}, role: {role}")
    except psycopg2.Error as e: # Captura erros específicos do psycopg2
        print(f"ERRO DB: Falha ao inserir mensagem para user_id {user_id}. Erro: {e}")
        if conn:
            conn.rollback() # Desfaz a transação em caso de erro
        raise # Re-lança a exceção
    except Exception as e: # Captura quaisquer outras exceções inesperadas
        print(f"ERRO INESPERADO: Falha ao inserir mensagem para user_id {user_id}. Erro: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        put_db_connection(conn)

def buscar_historico(user_id):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""SELECT role, messages FROM tabelademensagens WHERE user_id=%s ORDER BY id DESC LIMIT 20""", (user_id,))
        mensagens = cur.fetchall()
        mensagens.reverse()
        print(f"Histórico buscado para user_id: {user_id}")
        return [{"role": role, "content": msg} for role, msg in mensagens]
    except psycopg2.Error as e:
        print(f"ERRO DB: Falha ao buscar histórico para user_id {user_id}. Erro: {e}")
        raise
    except Exception as e:
        print(f"ERRO INESPERADO: Falha ao buscar histórico para user_id {user_id}. Erro: {e}")
        raise
    finally:
        if cur:
            cur.close()
        put_db_connection(conn)

def deletar_historico(user_id):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM tabelademensagens WHERE user_id=%s", (user_id,))
        conn.commit()
        print(f"Histórico deletado para user_id: {user_id}")
    except psycopg2.Error as e:
        print(f"ERRO DB: Falha ao deletar histórico para user_id {user_id}. Erro: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(f"ERRO INESPERADO: Falha ao deletar histórico para user_id {user_id}. Erro: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        put_db_connection(conn)
