from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from .deps import get_current_user
from .storage import upload_file_to_cos
from supabase import create_client
from .config import SUPABASE_URL,SUPABASE_SERVICE_KEY
#上传接口
router = APIRouter(prefix="/items", tags=["items"])
#创建supabase客户端
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

@router.post("/upload")
async def upload_item(
    #接口接受文件上传
    file: UploadFile = File(...),
    user = Depends(get_current_user),
):
    #  校验文件类型，只允许image/*
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    #  读取文件成二进制
    file_bytes = await file.read()

    #  上传到 COS
    try:
        image_url = upload_file_to_cos(
            user_id=str(user.id),
            file_bytes=file_bytes,
            original_filename=file.filename,
            content_type=file.content_type,
        )
    except Exception as e:
        print(">>> UPLOAD ERROR:",repr(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    #   写入数据库
    try:
        res = supabase.table("items").insert({
            "user_id": str(user.id),
            "image_url": image_url,
        }).execute()
        item_id = res.data[0]["id"] if res.data else None
    except Exception as e:
        print(">>> DB ERROR:",repr(e))
        raise HTTPException(status_code=500, detail=f"DB failed: {str(e)}")


    return {
        "message": "上传成功",
        "image_url": image_url,
    }
