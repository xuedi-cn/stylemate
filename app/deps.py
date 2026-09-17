from fastapi import Header, HTTPException
from supabase import create_client
from .config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_current_user(x_token: str = Header(None)):
    if not x_token or not x_token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = x_token.replace("Bearer ", "")

    try:
        res = supabase.auth.get_user(token)
        if not res.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return res.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")