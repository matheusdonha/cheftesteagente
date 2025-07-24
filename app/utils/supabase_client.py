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


def upload_file_to_supabase(file_path: str, bucket_name: str, file_name: str) -> str:
    """
    Faz o upload de um arquivo para o Supabase Storage e retorna a URL pública.

    :param file_path: O caminho do arquivo local a ser enviado.
    :param bucket_name: O nome do bucket no Supabase.
    :param file_name: O nome que o arquivo terá no Supabase.
    :return: A URL pública do arquivo, ou None em caso de erro.
    Se o arquivo já existir, ele será sobrescrito.
    """
    try:
        with open(file_path, 'rb') as f:
            # Faz o upload do arquivo
            try:
                supabase.storage.from_(bucket_name).upload(file_name, f)
                print(f"Arquivo {file_name} carregado com sucesso.", file=sys.stderr)

            except Exception as e:
                # Se for um erro 409 (Duplicate), tenta atualizar/sobrescrever
                # Note: Supabase Storage SDK pode retornar o erro de forma diferente
                # então verificamos a mensagem para um 409
                if "409" in str(e) or "Duplicate" in str(e):
                    f.seek(0)  # Volta o ponteiro do arquivo para o início para re-leitura
                    supabase.storage.from_(bucket_name).update(file_name, f)
                    print(f"Arquivo {file_name} atualizado (sobrescrito) com sucesso.", file=sys.stderr)
                else:
                    raise e  # Re-lança outras exceções

                # Obtém a URL pública do arquivo
            res = supabase.storage.from_(bucket_name).get_public_url(file_name)

            return res

    except Exception as e:
        print(f"Erro ao fazer upload ou atualizar para o Supabase: {e}", file=sys.stderr)
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

