"""FastAPI app entrypoint."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

import sentry_sdk
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration

from phongthuy_bds import __version__
from phongthuy_bds.api.v1.router import api_router
from phongthuy_bds.core.config import get_settings
from phongthuy_bds.core.logging import get_logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    log = get_logger("startup")
    log.info("api.starting", version=__version__, env=settings.env)
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.env,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.1 if settings.is_prod else 1.0,
        )
        log.info("sentry.initialized")
    yield
    log.info("api.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Phong Thủy BĐS API",
        description=(
            "Plug-in phong thủy cho môi giới bất động sản VN.\n\n"
            "**Bảo mật**: JWT bearer token, multi-tenant.\n"
            "**Tuân thủ**: NĐ 13/2023/NĐ-CP, Luật Đất đai 2024."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[JSONResponse]],
    ) -> JSONResponse:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.unbind_contextvars("request_id")
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        log = get_logger("api")
        log.exception("unhandled_exception", path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Lỗi hệ thống. Vui lòng thử lại hoặc liên hệ hỗ trợ.",
                "type": type(exc).__name__,
            },
        )

    app.include_router(api_router)

    @app.get("/", response_class=PlainTextResponse, include_in_schema=False)
    def root() -> str:
        return f"Phong Thủy BĐS API v{__version__} — xem /docs"

    return app


app = create_app()


def run() -> None:
    """`phongthuy-bds-api` console entry point."""
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "phongthuy_bds.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.env == "dev",
        log_config=None,
    )


if __name__ == "__main__":
    run()
