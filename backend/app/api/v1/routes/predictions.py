import logging
from typing import Any
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status, Request
from pydantic import BaseModel
from ...core.security import get_current_user, TokenPayload
from ...core.config import settings
from ...services.supabase_client import supabase, client_for_user
from ...services.inference import (
    get_inference_client,
    InferenceClient,
    Prediction,
    InferenceBadInput,
    InferenceGatewayError,
    InferenceTimeout,
)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png"}

router = APIRouter()
logger = logging.getLogger(__name__)


class PredictionResponse(BaseModel):
    prediction: Prediction
    image_url: str
    db: list[dict[str, Any]] | dict[str, Any] | None = None
    request_id: str


@router.post("/predictions", tags=["predictions"], response_model=PredictionResponse)
async def create_prediction(
    request: Request,
    file: UploadFile = File(...),
    user: TokenPayload = Depends(get_current_user),
    infer: InferenceClient = Depends(get_inference_client),
):
    if not file.content_type or file.content_type.lower() not in ALLOWED_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Only JPEG/PNG allowed")

    if not getattr(user, "access_token", None):
        logger.error("Authenticated user missing access token", extra={"user_id": user.sub})
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication context")

    user_client = client_for_user(user.access_token)
    storage = user_client.storage.from_(settings.STORAGE_BUCKET)
    admin_storage = supabase.storage.from_(settings.STORAGE_BUCKET)

    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty uploads are not allowed")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Max size 5 MB")

    # 1) Upload to private Storage
    object_path = f"{user.sub}/{uuid4()}_{file.filename}"
    try:
        storage.upload(object_path, data)
    except Exception:
        logger.exception("Storage upload failed", extra={"user_id": user.sub, "object_path": object_path})
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Unable to store image")

    # 2) Short-lived signed URL for ML
    try:
        ml_signed = admin_storage.create_signed_url(object_path, 120)  # 2 min for ML fetch
        ml_signed_url = ml_signed.get("signedURL") if isinstance(ml_signed, dict) else ml_signed
    except Exception:
        logger.exception("Failed to create ML signed URL", extra={"user_id": user.sub, "object_path": object_path})
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Unable to generate signed URL")

    # 3) Call ML service with signed URL
    req_id = request.headers.get("X-Request-ID") or str(uuid4())
    try:
        result = await infer.predict_from_url(ml_signed_url, request_id=req_id)
    except InferenceBadInput:
        logger.warning("Inference rejected payload", extra={"request_id": req_id, "user_id": user.sub})
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Model rejected the provided image")
    except InferenceTimeout:
        logger.warning("Inference timeout", extra={"request_id": req_id, "user_id": user.sub})
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "Inference service timeout")
    except InferenceGatewayError:
        logger.exception("Inference gateway error", extra={"request_id": req_id, "user_id": user.sub})
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Inference service unavailable")
    except Exception:
        logger.exception("Unexpected inference failure", extra={"request_id": req_id, "user_id": user.sub})
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Inference service failure")

    # 4) Longer signed URL for client viewing
    client_signed = admin_storage.create_signed_url(object_path, 60 * 60 * 24)  # 24h
    client_url = client_signed.get("signedURL") if isinstance(client_signed, dict) else client_signed

    # 5) Persist row
    row = {
        "user_id": user.sub,
        "image_path": object_path,
        "result": result.model_dump(),
        "confidence": result.confidence,
    }
    try:
        user_client.table("predictions").insert(row).execute()
    except Exception:
        logger.exception("Failed to persist prediction", extra={"user_id": user.sub, "request_id": req_id})
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Unable to save prediction")

    return PredictionResponse(
        prediction=result,
        image_url=client_url,
        request_id=req_id,
    )
