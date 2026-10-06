import json
import dashscope
from .config import DASHSCOPE_API_KEY
from .tools import query_items, query_style_refs, query_saved_outfits

dashscope.api_key = DASHSCOPE_API_KEY


def analyze_clothing(image_url: str) -> dict:
    """调用通义千问视觉模型分析单品图片"""
    prompt = """你是一个服装分析助手。请分析这张衣服图片，返回严格的 JSON（不要任何其他文字）：

{
  "category": "上衣/裤子/裙子/鞋/包/配饰",
  "color": "主要颜色（中文，如：黑色、白色、藏青）",
  "material": "材质（如：棉、麻、丝绸、牛仔、皮革）",
  "style_tags": ["风格标签，如：法式、极简、休闲、通勤、Y2K"],
  "season": "春季/夏季/秋季/冬季/四季"
}"""

    try:
        response = dashscope.MultiModalConversation.call(
            model="qwen3-vl-plus",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"image": image_url},
                        {"text": prompt},
                    ],
                }
            ],
        )

        if response.status_code != 200:
            raise Exception(f"AI API error: {response.message}")

        text = response.output.choices[0].message.content[0]["text"]

        # 清理 markdown 代码块标记
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        return json.loads(text)

    except Exception as e:
        print(">>> AI ERROR:", repr(e))
        raise
# ai分析风格参考图
def analyze_style(image_url: str) -> dict:
    """分析风格参考图，提取风格标签、主色调、关键单品"""
    prompt = """你是一个时尚风格分析师。请分析这张穿搭图片，返回严格的 JSON（不要任何其他文字）：

{
  "style_tags": ["风格标签，如：法式、极简、通勤、Y2K、复古、日系（3-5个）"],
  "colors": ["主色调，如：米白、黑色、藏青（2-3个）"],
  "key_items": ["关键单品，如：风衣、白衬衫、直筒裤（3-5个）"]
}"""

    try:
        response = dashscope.MultiModalConversation.call(
            model="qwen3-vl-plus",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"image": image_url},
                        {"text": prompt},
                    ],
                }
            ],
        )

        if response.status_code != 200:
            raise Exception(f"AI API error: {response.message}")

        text = response.output.choices[0].message.content[0]["text"]

        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        return json.loads(text)

    except Exception as e:
        print(">>> STYLE AI ERROR:", repr(e))
        raise


# ============ Agent 工具定义 ============

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_items",
            "description": "查询用户衣柜里的所有单品，返回品类、颜色、材质、风格标签、季节。推荐搭配前必须先调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户的 UUID"}
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_style_refs",
            "description": "查询用户上传的风格参考图标签，返回风格标签、主色调、关键单品。推荐搭配前必须调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户的 UUID"}
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_saved_outfits",
            "description": "查询用户保存过的搭配，了解用户喜欢的搭配风格，推荐时可以参考。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户的 UUID"}
                },
                "required": ["user_id"],
            },
        },
    },
]


# ============ Agent 主循环 ============

def recommend_outfits(user_id: str, scene: str) -> dict:
    """Agent 主函数：根据用户衣柜、风格偏好、收藏历史，推荐 3 套搭配。"""
    from .tools import query_items, query_style_refs, query_saved_outfits

    tool_map = {
        "query_items": query_items,
        "query_style_refs": query_style_refs,
    }

    # ★ 主动查询收藏（不通过工具，直接注入 prompt）
    try:
        saved = query_saved_outfits(user_id)
    except Exception as e:
        print(">>> query_saved_outfits failed:", repr(e))
        saved = []

    if saved:
        saved_text = "用户之前保存过的搭配（说明用户喜欢这种风格，推荐时可以参考）：\n"
        for s in saved[:5]:
            name = s.get("name") or "未命名"
            scene_ = s.get("scene") or "未知场景"
            reason = s.get("reason") or ""
            saved_text += f"- 【{name}】({scene_}): {reason}\n"
    else:
        saved_text = "（用户暂无收藏搭配）"

    system_prompt = f"""你是一个专业的 AI 造型师。根据用户的衣柜单品和风格偏好，为用户推荐 3 套搭配方案。

当前用户的 user_id 是：{user_id}
调用工具时，请使用这个 user_id，不要自己编造。

=== 用户收藏偏好 ===
{saved_text}
==================

要求：
1. 每套搭配从用户衣柜里选取 2-4 件单品组合
2. 必须使用衣柜里真实存在的单品 id
3. 每套搭配给出一个主题名和推荐理由
4. 如果用户有收藏偏好，推荐方向应尽量贴近用户喜欢的风格
5. 返回严格的 JSON 格式（不要任何其他文字）：
6.每套搭配必须**至少包含一件上装和一件下装**（或连衣裙）
7.如果当前用户的单品中有包包，鞋子，也可以加上鞋子，包包的搭配。
{{
  "outfits": [
    {{
      "name": "搭配主题（如：简约通勤风）",
      "item_ids": [1, 5, 8],
      "reason": "推荐理由，说明为什么适合这个场景、符合用户风格"
    }}
  ]
}}

请先调用工具获取用户的衣柜和风格偏好，再生成推荐。"""

    user_prompt = f"场景：{scene}。请为我推荐 3 套搭配。"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Agent 循环：最多 5 轮
    for _ in range(5):
        response = dashscope.Generation.call(
            model="qwen-plus",
            messages=messages,
            tools=AGENT_TOOLS,
            result_format="message",
        )

        if response.status_code != 200:
            raise Exception(f"Agent LLM error: {response.message}")

        msg = response.output.choices[0].message
        messages.append(msg)

        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            content = msg.get("content", "")
            return parse_final_answer(content)

        for tool_call in tool_calls:
            func_name = tool_call["function"]["name"]
            args = json.loads(tool_call["function"]["arguments"])

            if func_name in tool_map:
                result = tool_map[func_name](**args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result, ensure_ascii=False),
                })

    raise Exception("Agent 超过最大循环次数，未得到结果")

def parse_final_answer(content: str) -> dict:
    """解析 LLM 返回的最终答案（去掉 markdown 代码块）"""
    text = content.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


