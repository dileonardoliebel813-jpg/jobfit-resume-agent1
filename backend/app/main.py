from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    return app


app = create_app()
