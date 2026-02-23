from http import HTTPStatus

from aiohttp.web import Request, Response, json_response
from dependency_injector.wiring import Provide, inject

from common.types.interface import IHealthCheck
from service_crawler.src.container import Container


@inject
async def health(request: Request, service: IHealthCheck = Provide[Container.service]) -> Response:
    result = await service.is_healthy()
    if result:
        return json_response(status=HTTPStatus.OK)

    return json_response(status=HTTPStatus.GATEWAY_TIMEOUT)


@inject
async def ready(request: Request, service: IHealthCheck = Provide[Container.service]) -> Response:
    result = await service.is_ready()
    if result:
        return json_response(status=HTTPStatus.OK)

    return json_response(status=HTTPStatus.SERVICE_UNAVAILABLE)
