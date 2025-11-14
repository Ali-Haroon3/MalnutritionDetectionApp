from typing import Protocol, Optional, Dict, Any
import httpx
from pydantic import BaseModel
from ..core.config import settings


class Prediction(BaseModel):
    label: str
    confidence: float


class InferenceError(RuntimeError):
    """Base class for upstream inference failures."""


class InferenceBadInput(InferenceError):
    """Upstream model rejected the payload (treat as 400)."""


class InferenceGatewayError(InferenceError):
    """Generic upstream issues (treat as 502)."""


class InferenceTimeout(InferenceError):
    """Upstream timed out (treat as 504)."""


class InferenceClient(Protocol):
    async def predict_from_url(self, image_url: str, request_id: Optional[str] = None) -> Prediction: ...


class HttpInferenceClient:
    def __init__(self, base_url: str, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def predict_from_url(self, image_url: str, request_id: Optional[str] = None) -> Prediction:
        headers: Dict[str, str] = {}
        if settings.ML_API_KEY:
            headers["X-API-Key"] = settings.ML_API_KEY

        payload: Dict[str, Any] = {"image_url": image_url}
        if request_id:
            payload["request_id"] = request_id
            headers["X-Request-ID"] = request_id

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/infer", json=payload, headers=headers)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise InferenceTimeout("Inference service timeout") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in (400, 404, 409, 422):
                raise InferenceBadInput(f"Inference rejected payload ({status})") from exc
            raise InferenceGatewayError(f"Inference upstream error ({status})") from exc
        except httpx.RequestError as exc:
            raise InferenceGatewayError("Inference network failure") from exc

        body = response.json()
        pred = body.get("prediction") or body  # support both shapes
        return Prediction(**pred)


def get_inference_client() -> InferenceClient:
    if settings.ML_BASE_URL:
        return HttpInferenceClient(settings.ML_BASE_URL)

    class _Stub:
        async def predict_from_url(self, image_url: str, request_id: Optional[str] = None) -> Prediction:
            return Prediction(label="undetermined", confidence=0.0)

    return _Stub()
