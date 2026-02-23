import logging

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from common.logs.filters import OpenTelemetryLogFilter
from common.logs.formatters import ConsoleFormatter
from common.logs.interface import LoggerLike


class LoggerHandle:
    def __init__(
        self,
        name: str,
        is_export_enabled: bool,
        exporting_endpoint: str | None = None,
        level: int = logging.INFO,
    ) -> None:
        self._name = name
        self._level = level
        self._is_export_enabled = is_export_enabled
        self._exporting_endpoint = exporting_endpoint
        self._is_ready = False

        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._logger.handlers.clear()

        self.__setup_console_handler()
        self.__setup_export_handler()
        self._logger.propagate = False

    def __setup_console_handler(self) -> None:
        console_formatter = ConsoleFormatter()
        otel_filter = OpenTelemetryLogFilter()
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self._level)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(otel_filter)
        self._logger.addHandler(console_handler)

    def __setup_export_handler(self) -> None:
        if not self._is_export_enabled:
            return
        if not self._exporting_endpoint:
            raise ValueError("Exporting endpoint must be provided when export is enabled")

        self._provider = LoggerProvider(resource=Resource.create({"service.name": self._name}))

        set_logger_provider(self._provider)
        self._exporter = OTLPLogExporter(insecure=True, endpoint=self._exporting_endpoint)
        self._provider.add_log_record_processor(BatchLogRecordProcessor(self._exporter))
        handler = LoggingHandler(level=logging.NOTSET, logger_provider=self._provider)
        self._logger.addHandler(handler)

    async def start(self) -> None:
        self._logger.info(
            "Logging is enabled. Exporting is %s",
            f"enabled to '{self._exporting_endpoint}'" if self._is_export_enabled else "disabled",
        )
        self._is_ready = True

    async def stop(self) -> None:
        self._logger.info("Stopping logger...")
        if hasattr(self, "_exporter"):
            self._exporter.shutdown(timeout_millis=1000)
        self._is_ready = False

    async def is_healthy(self) -> bool:
        if not self._is_ready:
            return False
        return True

    async def is_ready(self) -> bool:
        return self._is_ready

    @property
    def logger(self) -> LoggerLike:
        return self._logger
