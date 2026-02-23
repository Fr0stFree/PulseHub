from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.metrics import Meter, set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

from common.logs.interface import LoggerLike


class MetricsExporter:
    def __init__(self, name: str, is_enabled: bool, endpoint: str, logger: LoggerLike) -> None:
        self._name = name
        self._endpoint = endpoint
        self._logger = logger
        self._is_enabled = is_enabled
        self._is_ready = False

        self._exporter: OTLPMetricExporter
        self._reader: PeriodicExportingMetricReader
        self._provider: MeterProvider

    async def start(self) -> None:
        if not self._is_enabled:
            self._logger.info("Metrics exporter is disabled")
            return

        resource = Resource.create({"service.name": self._name})
        self._exporter = OTLPMetricExporter(endpoint=self._endpoint, insecure=True)
        self._reader = PeriodicExportingMetricReader(self._exporter, export_interval_millis=5000)
        self._provider = MeterProvider(resource=resource, metric_readers=[self._reader])
        set_meter_provider(self._provider)
        self._logger.info("Metrics exporter is enabled to '%s'", self._endpoint)
        self._is_ready = True

    async def stop(self) -> None:
        if not self._is_enabled:
            return

        self._logger.info("Stopping metrics exporter...")
        self._reader.shutdown()
        self._exporter.shutdown()
        self._is_ready = False

    async def is_healthy(self) -> bool:
        return True

    async def is_ready(self) -> bool:
        if not self._is_enabled:
            return True
        return self._is_ready

    @property
    def meter(self) -> Meter:
        return self._provider.get_meter(self._name)
