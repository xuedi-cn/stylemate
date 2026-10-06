from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from supabase import create_client
from .config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from .deps import get_current_user
from .storage import upload_file_to_cos
from .ai import analyze_style

router = APIRouter(prefix="/styles", tags=["styles"])

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def analyze_and_update_style(style_id: int, image_url: str):
    """后台任务：分析风格图，把结果写回 style_refs"""
    try:
        result = analyze_style(image_url)
        supabase.table("style_refs").update({
            "style_tags": result.get("style_tags"),
            "colors": result.get("colors"),
            "key_items": result.get("key_items"),
        }).eq("id", style_id).execute()
        print(f">>> Style analysis done for style {style_id}")
    except Exception as e:
        print(f">>> Style analysis failed for style {style_id}: {repr(e)}")


@router.post("/upload")
async def upload_style(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user = Depends(get_current_user),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    file_bytes = await file.read()

    try:
        image_url = upload_file_to_cos(
            user_id=str(user.id),
            file_bytes=file_bytes,
            original_filename=file.filename,
            content_type=file.content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    try:
        res = supabase.table("style_refs").insert({
            "user_id": str(user.id),
            "image_url": image_url,
        }).execute()
        style_id = res.data[0]["id"] if res.data else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB failed: {str(e)}")

    background_tasks.add_task(analyze_and_update_style, style_id, image_url)

    return {
        "message": "上传成功，AI 分析中",
        "style_id": style_id,
        "image_url": image_url,
    }


@router.get("/")
def list_styles(user = Depends(get_current_user)):
    try:
        res = supabase.table("style_refs") \
            .select("id, image_url, style_tags, colors, key_items, created_at") \
            .eq("user_id", str(user.id)) \
            .order("created_at", desc=True) \
            .execute()
        return {
            "styles": res.data,
            "total": len(res.data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@router.delete("/{style_id}")
def delete_style(style_id: int, user = Depends(get_current_user)):
    """删除用户的风格参考图"""
    try:
        res = supabase.table("style_refs") \
            .select("id, user_id") \
            .eq("id", style_id) \
            .eq("user_id", str(user.id)) \
            .execute()

        if not res.data:
            raise HTTPException(status_code=404, detail="风格图不存在或不属于你")

        supabase.table("style_refs").delete().eq("id", style_id).execute()
        return {"message": "删除成功", "style_id": style_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")