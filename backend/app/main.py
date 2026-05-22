from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import ats, export, jd, match, profile, resume
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(jd.router, prefix=settings.API_V1_PREFIX)
    app.include_router(profile.router, prefix=settings.API_V1_PREFIX)
    app.include_router(match.router, prefix=settings.API_V1_PREFIX)
    app.include_router(resume.router, prefix=settings.API_V1_PREFIX)
    app.include_router(ats.router, prefix=settings.API_V1_PREFIX)
    app.include_router(export.router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    static_dir = Path(__file__).resolve().parent / "static"
    index_file = static_dir / "index.html"
    assets_dir = static_dir / "assets"

    if index_file.exists():
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/", include_in_schema=False)
        def serve_frontend() -> FileResponse:
            return FileResponse(index_file)

        @app.get("/{path:path}", include_in_schema=False)
        def serve_spa(path: str) -> FileResponse:
            if path.startswith(("api/", "docs", "redoc", "openapi.json")):
                raise HTTPException(status_code=404, detail="Not found")
            requested_file = static_dir / path
            if requested_file.is_file():
                return FileResponse(requested_file)
            return FileResponse(index_file)

    return app


app = create_app()
