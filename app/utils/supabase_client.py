from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv() # Carrega as variáveis do arquivo .env

# Suas credenciais do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Verifica se as credenciais existem
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("As variáveis de ambiente SUPABASE_URL e SUPABASE_ANON_KEY devem ser configuradas.")

# Inicializa o cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def upload_file_to_supabase(file_path: str, bucket_name: str, file_name: str) -> str:
    """
    Faz o upload de um arquivo para o Supabase Storage e retorna a URL pública.

    :param file_path: O caminho do arquivo local a ser enviado.
    :param bucket_name: O nome do bucket no Supabase.
    :param file_name: O nome que o arquivo terá no Supabase.
    :return: A URL pública do arquivo, ou None em caso de erro.
    """
    try:
        with open(file_path, 'rb') as f:
            # Faz o upload do arquivo
            supabase.storage.from_(bucket_name).upload(file_name, f)

            # Obtém a URL pública do arquivo
            res = supabase.storage.from_(bucket_name).get_public_url(file_name)

            return res

    except Exception as e:
        print(f"Erro ao fazer upload para o Supabase: {e}")
        return None


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

