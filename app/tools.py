from supabase import create_client
from .config import SUPABASE_URL, SUPABASE_SERVICE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def query_items(user_id: str) -> list:
    """查询用户的衣柜单品（只返回 AI 需要的字段）"""
    res = supabase.table("items") \
        .select("id, category, color, material, style_tags, season") \
        .eq("user_id", user_id) \
        .execute()
    return res.data or []


def query_style_refs(user_id: str) -> list:
    """查询用户的风格参考图标签"""
    res = supabase.table("style_refs") \
        .select("id, style_tags, colors, key_items") \
        .eq("user_id", user_id) \
        .execute()
    return res.data or []

def query_saved_outfits(user_id: str) -> list:
    """查询用户保存的搭配，作为风格偏好参考"""
    res = supabase.table("outfits") \
        .select("main_item_ids, alternatives, scene") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(10) \
        .execute()

    saved = []
    for outfit in res.data or []:
        alt = outfit.get("alternatives") or {}
        saved.append({
            "name": alt.get("name"),
            "reason": alt.get("reason"),
            "scene": outfit.get("scene"),
            "item_ids": outfit.get("main_item_ids"),
        })
    return saved