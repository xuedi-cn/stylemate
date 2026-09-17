from fastapi import FastAPI
from .config import SUPABASE_URL
from .auth import router as auth_router
#创建应用实例
app = FastAPI(title="StyleMate API")
#将auth路由挂到app
app.include_router(auth_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "stylemate",
        "supabase_configured": bool(SUPABASE_URL)
    }