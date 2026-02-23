from concurrent.futures import ThreadPoolExecutor

from grpc.aio import Server, ServerInterceptor, server

from common.grpc.interface import IRPCServicer
from common.logs import LoggerLike
from common.utils.backoff import AsyncBackoff


class GRPCServer:
    def __init__(
        self,
        worker_amount: int,
        port: int,
        logger: LoggerLike,
    ) -> None:
        self._port = port
        self._worker_amount = worker_amount
        self._logger = logger
        self._interceptors: list[ServerInterceptor] = []
        self._server: Server
        self._servicer: IRPCServicer
        self._is_ready = False

    def setup_servicer(self, servicer: IRPCServicer) -> None:
        self._servicer = servicer

    def add_interceptor(self, interceptor: ServerInterceptor) -> None:
        self._interceptors.append(interceptor)

    async def start(self) -> None:
        self._logger.info("Starting the grpc server on port %d...", self._port)
        self._server = server(ThreadPoolExecutor(max_workers=self._worker_amount), interceptors=self._interceptors)
        self._servicer.add_to_server(self._server)
        self._server.add_insecure_port(f"0.0.0.0:{self._port}")
        backoff = AsyncBackoff(name="gRPC server", logger=self._logger)
        await backoff.run(lambda: self._server.start())
        self._is_ready = True

    async def stop(self) -> None:
        self._logger.info("Shutting down the grpc server...")
        await self._server.stop(1)
        self._is_ready = False

    async def is_healthy(self) -> bool:
        # TODO: need something more useful
        if not self._is_ready:
            return False
        return True

    async def is_ready(self) -> bool:
        return self._is_ready
