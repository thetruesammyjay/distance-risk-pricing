from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.api_gateway.app.application import route_response
from services.api_gateway.app.config import get_settings
from services.api_gateway.app.dependencies import build_fare_service
from services.api_gateway.app.schemas import FareEstimateRequest, RouteResponse
from services.common.errors import DomainError
from services.routing_service.models import Coordinates

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(message)s")
logger = logging.getLogger(settings.app_name)

app = FastAPI(
    title="Distance-Risk-Aware Dynamic Pricing API",
    version="0.1.0",
    description="Research prototype API for explainable distance-risk-aware fare estimation.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.frontend_url.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

fare_service = build_fare_service(settings)
router = APIRouter(prefix="/api/v1")


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
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


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The request is invalid.",
                "details": exc.errors(),
            }
        },
    )


@app.get("/health", response_model=dict[str, str])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "version": "0.1.0"}


@router.post("/routes/estimate", response_model=RouteResponse)
async def estimate_route(request: FareEstimateRequest) -> RouteResponse:
    route = await fare_service.routing.estimate(
        Coordinates(request.origin.latitude, request.origin.longitude),
        Coordinates(request.destination.latitude, request.destination.longitude),
    )
    return route_response(route)


@router.post("/risk/estimate")
async def estimate_risk(request: FareEstimateRequest):
    route = await fare_service.routing.estimate(
        Coordinates(request.origin.latitude, request.origin.longitude),
        Coordinates(request.destination.latitude, request.destination.longitude),
    )
    del route
    risk = fare_service.risk.assess(
        (request.origin.latitude, request.origin.longitude),
        (request.destination.latitude, request.destination.longitude),
        request.requested_at,
    )
    return {
        "score": float(risk.score),
        "classification": risk.classification,
        "components": {key: float(value) for key, value in vars(risk.components).items()},
        "components_available": list(risk.components_available),
        "components_missing": list(risk.components_missing),
        "weight_strategy": risk.weight_strategy,
        "data_sources": list(risk.data_sources),
        "model_version": risk.model_version,
    }


@router.post("/fares/estimate")
async def estimate_fare(request: FareEstimateRequest):
    return await fare_service.estimate(request)


@router.get("/fares/{quote_id}")
async def get_fare(quote_id: str):
    quote = await fare_service.repository.get(quote_id)
    if quote is None:
        raise DomainError("QUOTE_NOT_FOUND", "The requested fare quote does not exist.")
    return quote


app.include_router(router)
