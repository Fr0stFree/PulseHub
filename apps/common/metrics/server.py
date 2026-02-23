from threading import Thread
from wsgiref.simple_server import WSGIServer

from prometheus_client import start_http_server

from common.logs import LoggerLike


class MetricsServer:
    def __init__(self, port: int, logger: LoggerLike) -> None:
        self._port = port
        self._logger = logger
        self._is_ready = False

        self._server: WSGIServer
        self._thread: Thread

    async def start(self) -> None:
        self._logger.info("Starting the metrics server on port %d...", self._port)
        self._server, self._thread = start_http_server(self._port)
        self._is_ready = True

    async def stop(self) -> None:
        self._logger.info("Shutting down the metrics server...")
        self._server.shutdown()
        self._thread.join()
        self._is_ready = False

    async def is_ready(self) -> bool:
        return self._is_ready

    async def is_healthy(self) -> bool:
        if not self._is_ready:
            return False
        return self._thread.is_alive()
