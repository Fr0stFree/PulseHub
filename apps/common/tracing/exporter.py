from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from common.logs import LoggerLike


class TraceExporter:
    def __init__(self, name: str, endpoint: str, is_enabled: bool, logger: LoggerLike) -> None:
        self._name = name
        self._endpoint = endpoint
        self._is_enabled = is_enabled
        self._logger = logger
        self._is_ready = False

        self._provider: TracerProvider
        self._exporter: OTLPSpanExporter

    async def start(self) -> None:
        if not self._is_enabled:
            self._logger.info("Trace exporter is disabled")
            return

        resource = Resource.create({"service.name": self._name})
        self._exporter = OTLPSpanExporter(endpoint=self._endpoint, insecure=True)
        self._provider = TracerProvider(resource=resource)
        self._provider.add_span_processor(BatchSpanProcessor(self._exporter))
        self._logger.info("Tracing exporter is enabled to '%s'", self._endpoint)
        trace.set_tracer_provider(self._provider)
        self._is_ready = True

    async def stop(self) -> None:
        self._logger.info("Stopping trace exporter...")
        self._provider.shutdown()
        self._exporter.shutdown()
        self._is_ready = False

    async def is_ready(self) -> bool:
        if not self._is_enabled:
            return True
        return self._is_ready

    async def is_healthy(self) -> bool:
        if not self._is_enabled:
            return True

        if not self._is_ready:
            return False

        return True
