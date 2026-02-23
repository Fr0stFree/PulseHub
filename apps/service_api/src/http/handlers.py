from http import HTTPStatus
from json import JSONDecodeError

from aiohttp.web import Request, Response, RouteTableDef, json_response
from dependency_injector.wiring import Provide, inject
from google.protobuf.json_format import MessageToDict
from opentelemetry.trace import Span

from common.grpc.client import GRPCClient
from common.service.service import BaseService
from protocol.analyzer_pb2 import (
    DeleteTargetRequest,
    GetTargetDetailsRequest,
    ListTargetsRequest,
)
from protocol.analyzer_pb2_grpc import AnalyzerServiceStub
from protocol.crawler_pb2 import AddTargetRequest, RemoveTargetRequest
from protocol.crawler_pb2_grpc import CrawlerServiceStub
from service_api.src.container import Container

routes = RouteTableDef()


@routes.get("/health")
@inject
async def health(request: Request, service: BaseService = Provide[Container.service]) -> Response:
    result = await service.is_healthy()
    if result:
        return json_response(status=HTTPStatus.OK)

    return json_response(status=HTTPStatus.GATEWAY_TIMEOUT)


@routes.get("/ready")
@inject
async def ready(request: Request, service: BaseService = Provide[Container.service]) -> Response:
    result = await service.is_ready()
    if result:
        return json_response(status=HTTPStatus.OK)

    return json_response(status=HTTPStatus.SERVICE_UNAVAILABLE)


@routes.post("/targets")
@inject
async def add_target(
    request: Request, crawler: GRPCClient[CrawlerServiceStub] = Provide[Container.crawler_client]
) -> Response:
    try:
        body = await request.json()
    except JSONDecodeError:
        return json_response({"error": "Invalid JSON body"}, status=HTTPStatus.BAD_REQUEST)

    target_url = body.get("targetUrl")
    if not target_url:
        return json_response({"error": "missing targetUrl field"}, status=HTTPStatus.BAD_REQUEST)

    rpc_request = AddTargetRequest(target_url=target_url)
    async with crawler as client:
        await client.AddTarget(rpc_request)

    return Response(status=HTTPStatus.CREATED)


@routes.get("/targets/{target_id}")
@inject
async def get_target(
    request: Request,
    analyzer: GRPCClient[AnalyzerServiceStub] = Provide[Container.analyzer_client],
) -> Response:
    target_id = request.match_info.get("target_id")
    if not target_id:
        return json_response({"error": "missing url id in path"}, status=HTTPStatus.BAD_REQUEST)

    rpc_request = GetTargetDetailsRequest(id=target_id)
    async with analyzer as client:
        rpc_response = await client.GetTargetDetails(rpc_request)

    response_body = MessageToDict(rpc_response, preserving_proto_field_name=True)
    return json_response(response_body, status=HTTPStatus.OK)


@routes.get("/targets")
@inject
async def list_targets(
    request: Request,
    analyzer: GRPCClient[AnalyzerServiceStub] = Provide[Container.analyzer_client],
    pagination_default_limit: int = Provide[Container.settings.pagination_default_limit],
    span: Span = Provide[Container.current_span],
) -> Response:
    limit = request.query.get("limit", pagination_default_limit)
    offset = request.query.get("offset", 0)

    span.set_attribute("pagination.limit", limit)
    span.set_attribute("pagination.offset", offset)

    rpc_request = ListTargetsRequest(limit=int(limit), offset=int(offset))
    async with analyzer as client:
        rpc_response = await client.ListTargets(rpc_request)

    response_body = MessageToDict(rpc_response)
    return json_response(response_body, status=HTTPStatus.OK)


@routes.delete("/targets/{target_id}")
@inject
async def delete_target(
    request: Request,
    crawler: GRPCClient[CrawlerServiceStub] = Provide[Container.crawler_client],
    analyzer: GRPCClient[AnalyzerServiceStub] = Provide[Container.analyzer_client],
) -> Response:
    target_id = request.match_info.get("target_id")
    if not target_id:
        return json_response({"error": "missing url id in path"}, status=HTTPStatus.BAD_REQUEST)

    rpc_request = GetTargetDetailsRequest(id=target_id)
    async with analyzer as client:
        rpc_response = await client.GetTargetDetails(rpc_request)

    target = rpc_response.target

    rpc_request = RemoveTargetRequest(target_url=target.url)
    async with crawler as client:
        await client.RemoveTarget(rpc_request)

    rpc_request = DeleteTargetRequest(id=target.id)
    async with analyzer as client:
        await client.DeleteTarget(rpc_request)

    return Response(status=HTTPStatus.NO_CONTENT)
