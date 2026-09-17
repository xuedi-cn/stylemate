from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from .deps import get_current_user
from .storage import upload_file_to_cos
#上传接口
router = APIRouter(prefix="/items", tags=["items"])


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
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    #  返回 URL（还没写数据库，这一步先返回）
    return {
        "message": "上传成功",
        "image_url": image_url,
    }