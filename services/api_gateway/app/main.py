from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, FastAPI, Path, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.api_gateway.app.application import route_response
from services.api_gateway.app.config import Settings, get_settings
from services.api_gateway.app.dependencies import build_fare_service
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
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in runtime_settings.frontend_url.split(",")],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
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
    if not request_id or len(request_id) > 100:
        request_id = str(uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        (time.perf_counter() - started) * 1000,
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
    risk = service.risk.assess(
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


app = create_app()
