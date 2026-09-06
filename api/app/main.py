from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import accounts, auth, categories, dashboard, movements, people, platforms, vendors

app = FastAPI(
    title="Household Ledger API",
    description="Family bank and investment ledger with receipts and line items",
    version="2.0.0",
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

Path(settings.document_storage_path).mkdir(parents=True, exist_ok=True)

api = FastAPI()
api.include_router(auth.router)
api.include_router(people.router)
api.include_router(platforms.router)
api.include_router(accounts.router)
api.include_router(vendors.router)
api.include_router(categories.router)
api.include_router(movements.router)
api.include_router(dashboard.router)
app.mount("/api/v1", api)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
