import io
import uuid
from PIL import Image
from qcloud_cos import CosConfig, CosS3Client
from .config import (
    COS_SECRET_ID,
    COS_SECRET_KEY,
    COS_BUCKET,
    COS_REGION,
)

config = CosConfig(
    Region=COS_REGION,
    SecretId=COS_SECRET_ID,
    SecretKey=COS_SECRET_KEY,
)
cos_client = CosS3Client(config)


def generate_cos_key(user_id: str, ext: str = "jpg") -> str:
    return f"{user_id}/{uuid.uuid4()}.{ext}"


def upload_file_to_cos(user_id: str, file_bytes: bytes, original_filename: str, content_type: str = "image/jpeg") -> str:
    # 统一转成 JPG
    img = Image.open(io.BytesIO(file_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85)
    jpg_bytes = output.getvalue()

    key = generate_cos_key(user_id, "jpg")

    cos_client.put_object(
        Bucket=COS_BUCKET,
        Body=jpg_bytes,
        Key=key,
        ContentType="image/jpeg",  # 明确告诉 COS 这是 JPEG 图片
    )

    return f"https://{COS_BUCKET}.cos.{COS_REGION}.myqcloud.com/{key}"