import asyncio
from http import HTTPMethod

from dependency_injector.wiring import Provide, inject

from common.brokers.interface import IBrokerConsumer
from common.grpc.interface import IGRPCServer, IRPCServicer
from common.http import IHTTPServer
from common.service import IService
from service_analyzer.src.consumer.handlers import on_new_message
from service_analyzer.src.consumer.interceptors import ObservabilityConsumerInterceptor
from service_analyzer.src.container import Container
from service_analyzer.src.grpc.interceptors import ObservabilityServerInterceptor
from service_analyzer.src.http import handlers


@inject
async def main(
    service: IService = Provide[Container.service],
    http_server: IHTTPServer = Provide[Container.http_server],
    grpc_server: IGRPCServer = Provide[Container.grpc_server],
    rpc_servicer: IRPCServicer = Provide[Container.rpc_servicer],
    consumer: IBrokerConsumer = Provide[Container.broker_consumer],
) -> None:
    http_server.add_handler(path="/health", handler=handlers.health, method=HTTPMethod.GET)
    http_server.add_handler(path="/ready", handler=handlers.ready, method=HTTPMethod.GET)
    consumer.add_interceptor(ObservabilityConsumerInterceptor())
    consumer.set_message_handler(on_new_message)
    grpc_server.setup_servicer(rpc_servicer)
    grpc_server.add_interceptor(ObservabilityServerInterceptor())
    await service.run()


if __name__ == "__main__":
    container = Container()
    container.wire(packages=["."], modules=[__name__])
    asyncio.run(main())
