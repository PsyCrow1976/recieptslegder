from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import accounts, auth, categories, dashboard, movements, people, platforms, vendors

STATIC_DIR = Path("/app/static")

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

Path(settings.document_storage_path).mkdir(parents=True, exist_ok=True)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(people.router, prefix="/api/v1")
app.include_router(platforms.router, prefix="/api/v1")
app.include_router(accounts.router, prefix="/api/v1")
app.include_router(vendors.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(movements.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if STATIC_DIR.is_dir():
    assets = STATIC_DIR / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        static_root = STATIC_DIR.resolve()
        candidate = (STATIC_DIR / full_path).resolve()
        if candidate.is_file() and candidate.is_relative_to(static_root):
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")
