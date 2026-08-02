import logging
import os
from urllib.parse import urlparse

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

SERVICE_NAME = "image-resizer"

load_dotenv("/etc/otel/env")


def grpc_target(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    return f"{parsed.hostname}:{parsed.port or 443}"


def grpc_headers(headers_env: str) -> tuple:
    key, _, value = headers_env.partition("=")
    return ((key.lower(), value),)


def setup_telemetry(app):
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    headers_env = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS")
    if not endpoint or not headers_env:
        logger.warning("OTEL_EXPORTER_OTLP_ENDPOINT/HEADERS not set, skipping tracing setup")
        return None

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=grpc_target(endpoint), headers=grpc_headers(headers_env))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)

    return provider
