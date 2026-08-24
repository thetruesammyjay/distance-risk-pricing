from __future__ import annotations

import hmac
import logging
import time
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, FastAPI, Path, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from services.api_gateway.app.application import route_response
from services.api_gateway.app.config import Settings, get_settings
from services.api_gateway.app.dependencies import build_fare_service
from services.api_gateway.app.observability import MetricsRegistry, SlidingWindowRateLimiter
from services.api_gateway.app.schemas import (
    FareEstimateRequest,
    FareEstimateResponse,
    RiskResponse,
    RouteResponse,
)
from services.common.errors import DomainError
from services.routing_service.models import Coordinates

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(message)s")
logger = logging.getLogger(settings.app_name)

fare_service = build_fare_service(settings)
router = APIRouter(prefix="/api/v1")
health_router = APIRouter()


@asynccontextmanager
async def lifespan(application: FastAPI):
    yield
    close = getattr(application.state.fare_service, "close", None)
    if close is not None:
        await close()


def create_app(
    app_settings: Settings | None = None,
    service: object | None = None,
) -> FastAPI:
    runtime_settings = app_settings or settings
    runtime_service = service or fare_service
    application = FastAPI(
        title="Distance-Risk-Aware Dynamic Pricing API",
        version="0.1.0",
        description="Research prototype API for explainable distance-risk-aware fare estimation.",
        lifespan=lifespan,
    )
    application.state.settings = runtime_settings
    application.state.fare_service = runtime_service
    application.state.metrics = MetricsRegistry()
    application.state.rate_limiter = SlidingWindowRateLimiter(
        runtime_settings.rate_limit_requests, runtime_settings.rate_limit_window_seconds
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in runtime_settings.frontend_url.split(",")],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
    )
    application.middleware("http")(request_context)
    application.include_router(health_router)
    application.include_router(router)
    application.add_exception_handler(DomainError, domain_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.add_exception_handler(Exception, internal_error_handler)
    return application


async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", "").strip()
    if not request_id or len(request_id) > 100 or not all(
        character.isalnum() or character in "-_." for character in request_id
    ):
        request_id = str(uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    if _requires_auth(request) and not _authenticated(request):
        response = _security_response(
            401, "AUTHENTICATION_REQUIRED", "A valid API key is required."
        )
    elif _is_rate_limited(request) and not await request.app.state.rate_limiter.allow(
        _rate_limit_key(request)
    ):
        response = _security_response(
            429, "RATE_LIMITED", "Too many requests. Please retry later.", retry_after="60"
        )
    else:
        response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    duration = time.perf_counter() - started
    route = request.scope.get("route")
    metric_path = getattr(route, "path", request.url.path)
    await request.app.state.metrics.observe(
        request.method, metric_path, response.status_code, duration
    )
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        metric_path,
        response.status_code,
        duration * 1000,
    )
    return response


async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            "location": list(error.get("loc", ())),
            "message": error.get("msg", "The value is invalid."),
            "type": error.get("type", "validation_error"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The request is invalid.",
                "details": details,
            }
        },
    )


async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("request_id=%s unhandled_error=%s", request.state.request_id, exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "details": None,
            }
        },
    )


@health_router.get("/health", response_model=dict[str, str])
async def health(request: Request) -> dict[str, str]:
    app_settings = request.app.state.settings
    return {"status": "ok", "service": app_settings.app_name, "version": "0.1.0"}


@health_router.get("/ready", response_model=dict[str, object])
async def ready(request: Request) -> JSONResponse:
    checks = await request.app.state.fare_service.readiness()
    is_ready = all(checks.values())
    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={"status": "ready" if is_ready else "not_ready", "checks": checks},
    )


@health_router.get("/metrics", include_in_schema=False)
async def metrics(request: Request) -> Response:
    return Response(
        content=await request.app.state.metrics.render(),
        media_type="text/plain; version=0.0.4",
    )


@router.post("/routes/estimate", response_model=RouteResponse)
async def estimate_route(payload: FareEstimateRequest, request: Request) -> RouteResponse:
    service = request.app.state.fare_service
    route = await service.routing.estimate(
        Coordinates(payload.origin.latitude, payload.origin.longitude),
        Coordinates(payload.destination.latitude, payload.destination.longitude),
    )
    return route_response(route)


@router.post("/risk/estimate")
async def estimate_risk(payload: FareEstimateRequest, request: Request) -> RiskResponse:
    service = request.app.state.fare_service
    risk = await service.risk.assess(
        (payload.origin.latitude, payload.origin.longitude),
        (payload.destination.latitude, payload.destination.longitude),
        payload.requested_at,
    )
    return RiskResponse.model_validate(
        {
            "score": float(risk.score),
            "classification": risk.classification,
            "components": {
                key: float(value) if value is not None else None
                for key, value in vars(risk.components).items()
            },
            "components_available": list(risk.components_available),
            "components_missing": list(risk.components_missing),
            "weight_strategy": risk.weight_strategy,
            "source_type": risk.source_type,
            "data_sources": list(risk.data_sources),
            "model_version": risk.model_version,
        }
    )


@router.post("/fares/estimate", response_model=FareEstimateResponse)
async def estimate_fare(payload: FareEstimateRequest, request: Request) -> FareEstimateResponse:
    return await request.app.state.fare_service.estimate(payload)


@router.get("/fares/{quote_id}", response_model=FareEstimateResponse)
async def get_fare(
    quote_id: Annotated[UUID, Path(description="Persisted fare quote identifier")],
    request: Request,
) -> dict[str, object]:
    quote = await request.app.state.fare_service.repository.get(str(quote_id))
    if quote is None:
        raise DomainError("QUOTE_NOT_FOUND", "The requested fare quote does not exist.")
    return quote


def _requires_auth(request: Request) -> bool:
    return request.url.path.startswith("/api/v1/") or request.url.path == "/metrics"


def _authenticated(request: Request) -> bool:
    app_settings = request.app.state.settings
    if not app_settings.api_auth_enabled:
        return True
    supplied = request.headers.get("X-API-Key", "")
    configured = app_settings.api_key.get_secret_value() if app_settings.api_key else ""
    return bool(supplied and configured and hmac.compare_digest(supplied, configured))


def _is_rate_limited(request: Request) -> bool:
    return request.url.path.startswith("/api/v1/")


def _rate_limit_key(request: Request) -> str:
    client_host = request.client.host if request.client else "unknown"
    api_key = request.headers.get("X-API-Key", "")
    return f"{client_host}:{hash(api_key)}"


def _security_response(
    status_code: int,
    code: str,
    message: str,
    *,
    retry_after: str | None = None,
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": None}},
    )
    if retry_after:
        response.headers["Retry-After"] = retry_after
    return response


app = create_app()
