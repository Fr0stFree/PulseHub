from dependency_injector.wiring import Provide, inject
from google.protobuf.empty_pb2 import Empty
from grpc import StatusCode
from grpc.aio import Server, ServicerContext
from opentelemetry.trace import Span

from common.logs.interface import LoggerLike
from protocol.analyzer_pb2 import (
    GetTargetDetailsRequest,
    GetTargetDetailsResponse,
    ListTargetsRequest,
    ListTargetsResponse,
)
from protocol.analyzer_pb2_grpc import AnalyzerServiceServicer, add_AnalyzerServiceServicer_to_server
from service_analyzer.src.container import Container
from service_analyzer.src.db.repo import Repository


class RPCServicer(AnalyzerServiceServicer):
    @inject
    async def GetTargetDetails(
        self,
        request: GetTargetDetailsRequest,
        context: ServicerContext,
        repo: Repository = Provide[Container.repository],
        logger: LoggerLike = Provide[Container.logger],
        span: Span = Provide[Container.current_span],
    ) -> GetTargetDetailsResponse:
        target = await repo.get_target(request.id)
        if target is None:
            await context.abort(code=StatusCode.NOT_FOUND, details=f"Target with id '{request.id}' does not exist")

        span.set_attribute("target.url", target.url)
        return GetTargetDetailsResponse(target=target.to_proto())

    @inject
    async def ListTargets(
        self,
        request: ListTargetsRequest,
        context: ServicerContext,
        repo: Repository = Provide[Container.repository],
        logger: LoggerLike = Provide[Container.logger],
        span: Span = Provide[Container.current_span],
    ) -> ListTargetsResponse:
        targets = await repo.list_targets(limit=request.limit, offset=request.offset)
        proto_targets = [target.to_proto() for target in targets]
        span.set_attribute("targets.count", len(proto_targets))
        return ListTargetsResponse(targets=proto_targets)

    @inject
    async def DeleteTarget(
        self,
        request: GetTargetDetailsRequest,
        context: ServicerContext,
        repo: Repository = Provide[Container.repository],
        logger: LoggerLike = Provide[Container.logger],
        span: Span = Provide[Container.current_span],
    ) -> Empty:
        logger.info("Deleting target '%s'...", request.id)
        await repo.delete_target(request.id)
        span.set_attribute("target.id", request.id)
        return Empty()

    def add_to_server(self, server: Server) -> None:
        return add_AnalyzerServiceServicer_to_server(self, server)
