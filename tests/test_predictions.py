import io
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from httpx import AsyncClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.app.main import app
from backend.app.api.v1.routes import predictions as predictions_module
from backend.app.api.v1.routes.predictions import MAX_UPLOAD_BYTES
from backend.app.core.security import get_current_user, TokenPayload
from backend.app.services.inference import (
    Prediction,
    InferenceBadInput,
    InferenceGatewayError,
    InferenceTimeout,
    get_inference_client,
)


class _BucketMock:
    def __init__(self):
        self.uploaded = []
        self.signed = []

    def upload(self, path: str, data: bytes) -> None:
        self.uploaded.append((path, data))

    def create_signed_url(self, path: str, expires_in: int) -> dict[str, str]:
        self.signed.append((path, expires_in))
        return {"signedURL": f"https://storage.local/{path}?exp={expires_in}"}


class _StorageMock:
    def __init__(self):
        self.buckets: dict[str, _BucketMock] = {}

    def from_(self, bucket: str) -> _BucketMock:
        bucket_ref = self.buckets.setdefault(bucket, _BucketMock())
        return bucket_ref


class _TableMock:
    def __init__(self, name: str):
        self.name = name
        self.rows: list[dict] = []

    def insert(self, row: dict) -> "_TableMock":
        self.rows.append(row)
        return self

    def execute(self) -> SimpleNamespace:
        return SimpleNamespace(data=self.rows)


class SupabaseClientMock:
    def __init__(self):
        self.storage = _StorageMock()
        self.tables: dict[str, _TableMock] = {}

    def table(self, name: str) -> _TableMock:
        table = self.tables.setdefault(name, _TableMock(name))
        return table


class InferenceSpy:
    def __init__(self):
        self.error = None
        self.last_call: tuple[str, str | None] | None = None
        self.result = Prediction(label="healthy", confidence=0.9)

    async def predict_from_url(self, image_url: str, request_id: str | None = None) -> Prediction:
        self.last_call = (image_url, request_id)
        if self.error:
            raise self.error
        return self.result


@pytest.fixture(autouse=True)
def override_auth():
    def fake_user():
        return TokenPayload(sub="user-123", email="demo@example.com", raw={}, access_token="token-xyz")

    app.dependency_overrides[get_current_user] = fake_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(autouse=True)
def supabase_clients(monkeypatch):
    admin_client = SupabaseClientMock()
    user_client = SupabaseClientMock()

    monkeypatch.setattr(predictions_module, "supabase", admin_client)
    monkeypatch.setattr(predictions_module, "client_for_user", lambda token: user_client)
    return {"admin": admin_client, "user": user_client}


@pytest.fixture
def inference_spy():
    spy = InferenceSpy()
    app.dependency_overrides[get_inference_client] = lambda: spy
    yield spy
    app.dependency_overrides.pop(get_inference_client, None)


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


async def _post_image(client: AsyncClient, *, filename: str = "img.jpg", content: bytes = b"123", content_type: str = "image/jpeg"):
    files = {"file": (filename, io.BytesIO(content), content_type)}
    return await client.post("/api/v1/predictions", files=files)


@pytest.mark.asyncio
async def test_create_prediction_success(client, supabase_clients, inference_spy):
    response = await _post_image(client)
    assert response.status_code == 200
    body = response.json()
    assert body["prediction"]["label"] == "healthy"
    assert body["request_id"]
    assert body["db"] is None
    user_bucket = supabase_clients["user"].storage.from_("uploads")
    assert user_bucket.uploaded  # file made it to user-scoped storage
    user_table = supabase_clients["user"].table("predictions")
    assert user_table.rows[0]["user_id"] == "user-123"
    admin_bucket = supabase_clients["admin"].storage.from_("uploads")
    assert admin_bucket.uploaded == []  # service role only signing URLs
    assert inference_spy.last_call[0].startswith("https://storage.local")


@pytest.mark.asyncio
async def test_rejects_invalid_mime_type(client):
    response = await _post_image(client, filename="bad.gif", content_type="image/gif")
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_rejects_oversized_upload(client):
    payload = b"x" * (MAX_UPLOAD_BYTES + 1)
    response = await _post_image(client, content=payload)
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_maps_inference_bad_input(client, inference_spy):
    inference_spy.error = InferenceBadInput("bad payload")
    response = await _post_image(client)
    assert response.status_code == 400
    assert response.json()["detail"] == "Model rejected the provided image"


@pytest.mark.asyncio
async def test_maps_inference_gateway_error(client, inference_spy):
    inference_spy.error = InferenceGatewayError("upstream boom")
    response = await _post_image(client)
    assert response.status_code == 502
    assert response.json()["detail"] == "Inference service unavailable"


@pytest.mark.asyncio
async def test_maps_inference_timeout(client, inference_spy):
    inference_spy.error = InferenceTimeout("timed out")
    response = await _post_image(client)
    assert response.status_code == 504
    assert response.json()["detail"] == "Inference service timeout"
