from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import create_client
from .config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from .deps import get_current_user
from .ai import recommend_outfits
from typing import List

router = APIRouter(prefix="/outfits", tags=["outfits"])

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

@router.post("/recommend")
def recommend(scene: str, user = Depends(get_current_user)):
    result = recommend_outfits(str(user.id), scene)

    # 把 item_ids 换成完整单品信息
    for outfit in result.get("outfits", []):
        item_ids = outfit.get("item_ids", [])
        if item_ids:
            res = supabase.table("items") \
                .select("id, image_url, category, color, material, style_tags, season") \
                .in_("id", item_ids) \
                .eq("user_id", str(user.id)) \
                .execute()
            outfit["items"] = res.data or []
            del outfit["item_ids"]

    return result



class SaveOutfitRequest(BaseModel):
    name: str
    item_ids: List[int]
    reason: str
    scene: str = ""


@router.post("/save")
def save_outfit(req: SaveOutfitRequest, user = Depends(get_current_user)):
    """保存用户喜欢的搭配到「我的搭配」"""
    try:
        # 校验 item_ids 属于当前用户
        res = supabase.table("items") \
            .select("id") \
            .in_("id", req.item_ids) \
            .eq("user_id", str(user.id)) \
            .execute()
        if len(res.data) != len(req.item_ids):
            raise HTTPException(status_code=404, detail="部分单品不存在或不属于你")

        # 写入 outfits 表
        insert_res = supabase.table("outfits").insert({
            "user_id": str(user.id),
            "main_item_ids": req.item_ids,
            "scene": req.scene,
            "alternatives": {
                "name": req.name,
                "reason": req.reason,
            },
        }).execute()

        outfit_id = insert_res.data[0]["id"] if insert_res.data else None

        return {
            "message": "保存成功",
            "outfit_id": outfit_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/saved")
def list_saved_outfits(user = Depends(get_current_user)):
    """查询当前用户保存的所有搭配"""
    try:
        res = supabase.table("outfits") \
            .select("id, main_item_ids, alternatives, scene, created_at") \
            .eq("user_id", str(user.id)) \
            .order("created_at", desc=True) \
            .execute()

        # 把每个搭配的单品详情查出来
        outfits_with_items = []
        for outfit in res.data:
            item_ids = outfit.get("main_item_ids") or []
            items = []
            if item_ids:
                items_res = supabase.table("items") \
                    .select("id, image_url, category, color, material, style_tags, season") \
                    .in_("id", item_ids) \
                    .eq("user_id", str(user.id)) \
                    .execute()
                items = items_res.data or []

            outfits_with_items.append({
                "id": outfit["id"],
                "name": (outfit.get("alternatives") or {}).get("name"),
                "reason": (outfit.get("alternatives") or {}).get("reason"),
                "scene": outfit.get("scene"),
                "created_at": outfit.get("created_at"),
                "items": items,
            })

        return {
            "outfits": outfits_with_items,
            "total": len(outfits_with_items),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
#删除保存搭配
@router.delete("/{outfit_id}")
def delete_saved_outfit(outfit_id: int, user = Depends(get_current_user)):
    """删除用户保存的搭配"""
    try:
        # 先查这条是否属于当前用户
        res = supabase.table("outfits") \
            .select("id, user_id") \
            .eq("id", outfit_id) \
            .eq("user_id", str(user.id)) \
            .execute()

        if not res.data:
            raise HTTPException(status_code=404, detail="搭配不存在或不属于你")

        supabase.table("outfits").delete().eq("id", outfit_id).execute()

        return {"message": "删除成功", "outfit_id": outfit_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")