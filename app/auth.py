from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import create_client
from .config import SUPABASE_URL, SUPABASE_KEY
#路由分组
router = APIRouter(prefix="/auth", tags=["auth"])
#创建supabase客户端
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(req: AuthRequest):
    try:
        res = supabase.auth.sign_up({
            "email": req.email,
            "password": req.password
        })
        return {
            "message": "注册成功",
            "user_id": res.user.id if res.user else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(req: AuthRequest):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password
        })
        return {
            "message": "登录成功",
            "access_token": res.session.access_token if res.session else None,
            "user_id": res.user.id if res.user else None
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))