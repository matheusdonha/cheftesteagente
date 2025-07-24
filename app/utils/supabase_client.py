from dotenv import load_dotenv
import os
from supabase import create_client, Client
import sys

load_dotenv() # Carrega as variáveis do arquivo .env

# Suas credenciais do Supabase
SUPABASE_LIBRARY_URL = os.getenv("SUPABASE_LIBRARY_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Verifica se as credenciais existem
if not SUPABASE_LIBRARY_URL or not SUPABASE_ANON_KEY:
    raise ValueError("As variáveis de ambiente SUPABASE_DATABASE_URL e SUPABASE_ANON_KEY devem ser configuradas.")

# Inicializa o cliente Supabase
supabase: Client = create_client(SUPABASE_LIBRARY_URL, SUPABASE_ANON_KEY)


def upload_file_to_supabase(file_path: str, bucket_name: str, file_name: str) -> bool:
    """
    Faz o upload de um arquivo para o Supabase Storage.
    Retorna True se o upload/update foi bem-sucedido, False caso contrário.
    """
    try:
        with open(file_path, 'rb') as f:
            try:
                supabase.storage.from_(bucket_name).upload(file_name, f)
                print(f"Arquivo {file_name} carregado com sucesso.", file=sys.stderr)
            except Exception as e:
                if "409" in str(e) or "Duplicate" in str(e):
                    f.seek(0)
                    supabase.storage.from_(bucket_name).update(file_name, f)
                    print(f"Arquivo {file_name} atualizado (sobrescrito) com sucesso.", file=sys.stderr)
                else:
                    print(f"Erro ao fazer upload ou atualizar para o Supabase (fora do 409): {e}", file=sys.stderr)
                    return False # Retorna False em caso de erro
        return True # Retorna True se tudo ocorreu bem
    except Exception as e:
        print(f"Erro geral ao fazer upload para o Supabase: {e}", file=sys.stderr)
        return False # Retorna False em caso de erro

def get_public_url(bucket_name: str, file_name: str) -> str:
    """
    Retorna a URL pública de um arquivo já existente no Supabase Storage.

    :param bucket_name: O nome do bucket.
    :param file_name: O nome do arquivo no bucket.
    :return: A URL pública, ou uma string vazia se não for encontrado.
    """
    try:
        return supabase.storage.from_(bucket_name).get_public_url(file_name)
    except Exception as e:
        print(f"Erro ao obter URL pública do Supabase: {e}")
        return ""

