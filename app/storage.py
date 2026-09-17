import os
import uuid
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


def generate_cos_key(user_id: str, original_filename: str) -> str:
    ext = original_filename.split(".")[-1].lower()
    return f"{user_id}/{uuid.uuid4()}.{ext}"


def upload_file_to_cos(
        user_id: str,
        file_bytes: bytes,
        original_filename: str,
        content_type: str = "image/jpeg",
) -> str:
    key = generate_cos_key(user_id, original_filename)
    cos_client.put_object(
        Bucket=COS_BUCKET,
        Body=file_bytes,
        Key=key,
        ContentType=content_type,
    )
    return f"https://{COS_BUCKET}.cos.{COS_REGION}.myqcloud.com/{key}"