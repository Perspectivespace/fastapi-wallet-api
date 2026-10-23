from fastapi import FastAPI

from app.api.wallets import router as wallets_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(wallets_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
