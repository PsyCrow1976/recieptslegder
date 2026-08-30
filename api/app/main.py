from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, dashboard, receipts, tags

app = FastAPI(
    title="Receipts Ledger API",
    description="Personal Danish receipt ledger with Harald Nyborg scanning",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.receipt_storage_path).mkdir(parents=True, exist_ok=True)

api = FastAPI()
api.include_router(auth.router)
api.include_router(tags.router)
api.include_router(receipts.router)
api.include_router(dashboard.router)
app.mount("/api/v1", api)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
