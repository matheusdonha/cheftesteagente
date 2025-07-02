import sqlite3
import os
import requests

DB_PATH = "app/utils/historicomensagens.db"

#Criação da tabela (executar uma vez no início)
def inicializar_db():
    con=sqlite3.connect(DB_PATH)
    cur=con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tabelademensagens(
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        messages TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()

inicializar_db()

def enviar_mensagem_telegram(chat_id, texto):
    token = os.getenv('TELEGRAM_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id":chat_id , "text":texto}

    response = requests.post(url, json=payload)


def inserir_mensagem(user_id, role, messages):
    con=sqlite3.connect(DB_PATH)
    cur=con.cursor()
    cur.execute("""INSERT INTO tabelademensagens(user_id, role, messages) VALUES (?,?,?)""",
                (user_id, role, messages))
    con.commit()
    con.close()

def buscar_historico(user_id):
    con=sqlite3.connect(DB_PATH)
    cur=con.cursor()
    cur.execute("""SELECT role, messages FROM tabelademensagens WHERE user_id=? ORDER BY ROWID DESC LIMIT 20""", (user_id,))
    mensagens = cur.fetchall()
    con.close()
    mensagens.reverse()
    return [{"role": role, "content": msg} for role, msg in mensagens]

def deletar_historico(user_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM tabelademensagens WHERE user_id=?", (user_id,))
    con.commit()
    con.close()