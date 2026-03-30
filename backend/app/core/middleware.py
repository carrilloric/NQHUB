"""
Middleware for Prometheus metrics collection
AUT-360: Monitoring stack
"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from app.core.metrics import record_api_request


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically record metrics for all HTTP requests.
    Records method, endpoint, status code, and duration.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Start timing
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Extract endpoint without parameters
        endpoint = request.url.path
        method = request.method
        status = response.status_code

        # Record metrics
        record_api_request(
            method=method,
            endpoint=endpoint,
            status=status,
            duration=duration
        )

        return response