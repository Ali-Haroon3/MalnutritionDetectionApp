from fastapi import FastAPI
from .core.config import settings
from .api.v1.routes import health, predictions

app = FastAPI(title="Malnutrition Detection API", version=settings.VERSION)

api = FastAPI()
app.include_router(health.router, prefix=f"{settings.API_PREFIX}/v1")
app.include_router(predictions.router, prefix=f"{settings.API_PREFIX}/v1")
