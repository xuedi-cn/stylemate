import os
from dotenv import load_dotenv

load_dotenv()

#统一读取环境变量
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")


COS_SECRET_ID = os.getenv("COS_SECRET_ID")
COS_SECRET_KEY = os.getenv("COS_SECRET_KEY")
COS_BUCKET = os.getenv("COS_BUCKET")
COS_REGION = os.getenv("COS_REGION")