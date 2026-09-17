import os
from dotenv import load_dotenv

load_dotenv()

#统一读取环境变量
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")