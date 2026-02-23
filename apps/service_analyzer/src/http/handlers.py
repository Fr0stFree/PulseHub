from http import HTTPStatus

from aiohttp.web import Request, Response, json_response
from dependency_injector.wiring import Provide, inject

from common.service import IService
from service_analyzer.src.container import Container


@inject
async def health(request: Request, service: IService = Provide[Container.service]) -> Response:
    is_healthy = await service.is_healthy()
    if is_healthy:
        return json_response(status=HTTPStatus.OK)

    return json_response(status=HTTPStatus.GATEWAY_TIMEOUT)


@inject
async def ready(request: Request, service: IService = Provide[Container.service]) -> Response:
    is_ready = await service.is_ready()
    if is_ready:
        return json_response(status=HTTPStatus.OK)

    return json_response(status=HTTPStatus.SERVICE_UNAVAILABLE)
