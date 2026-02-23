import json
from uuid import uuid4

from aiokafka import AIOKafkaProducer

from common.brokers.interface import AbstractProducerInterceptor
from common.logs import LoggerLike
from common.utils.backoff import AsyncBackoff


class KafkaProducer:

    def __init__(
        self,
        topic: str,
        address: str,
        client_prefix: str,
        logger: LoggerLike,
    ) -> None:
        self._topic = topic
        self._address = address
        self._client_prefix = client_prefix
        self._logger = logger
        self._client_id = f"{client_prefix}-{uuid4().hex[:6]}"
        self._is_ready = False
        self._producer = AIOKafkaProducer(
            bootstrap_servers=address,
            client_id=self._client_id,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )
        self._interceptor: list[AbstractProducerInterceptor] = []

    def add_interceptor(self, interceptor: AbstractProducerInterceptor) -> None:
        self._interceptor.append(interceptor)

    async def start(self) -> None:
        self._logger.info(
            "Starting the kafka producer '%s' on server '%s' with topic '%s'...",
            self._client_id,
            self._address,
            self._topic,
        )
        backoff = AsyncBackoff(name=f"Kafka producer '{self._client_id}'", logger=self._logger)
        await backoff.run(lambda: self._producer.start())
        self._is_ready = True

    async def is_ready(self) -> bool:
        return self._is_ready

    async def is_healthy(self) -> bool:
        if not self._is_ready:
            return False
        await self._producer.partitions_for(self._topic)
        return True

    async def stop(self) -> None:
        self._logger.info("Shutting down the kafka producer '%s'...", self._client_id)
        await self._producer.stop()
        self._is_ready = False

    def _encode_headers(self, headers: dict[str, str]) -> list[tuple[str, bytes]]:
        return [(key, value.encode("utf-8")) for key, value in headers.items()]

    async def send(self, payload: dict, meta: dict) -> None:
        for interceptor in self._interceptor:
            await interceptor.before_send(self._topic, payload, meta)

        try:
            headers = self._encode_headers(meta)
            await self._producer.send_and_wait(self._topic, payload, headers=headers)
        except Exception as error:
            for interceptor in self._interceptor:
                await interceptor.on_error(self._topic, payload, meta, error)
            raise error

        for interceptor in self._interceptor:
            await interceptor.after_send(self._topic, payload, meta)
