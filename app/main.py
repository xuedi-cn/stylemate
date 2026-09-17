from fastapi import FastAPI,Depends
from .config import SUPABASE_URL
from .auth import router as auth_router
from .deps import get_current_user
from .items import router as items_router
#创建应用实例
app = FastAPI(title="StyleMate API")
#将auth路由挂到app
app.include_router(auth_router)
app.include_router(items_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "stylemate",
        "supabase_configured": bool(SUPABASE_URL)
    }
#获取当前用户信息
@app.get("/me")
def me(user = Depends(get_current_user)):
    return {
        "user_id": str(user.id),
        "email": user.user_metadata.get("email") if user.user_metadata else None
    }
