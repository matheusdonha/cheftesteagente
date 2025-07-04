from dotenv import load_dotenv
load_dotenv()

import os
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
SUPABASE_URL = os.environ.get('SUPABASE_URL')