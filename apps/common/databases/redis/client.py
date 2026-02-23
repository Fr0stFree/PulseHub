from contextlib import suppress

from opentelemetry.instrumentation.redis import RedisInstrumentor
from redis.asyncio import Redis

from common.logs import LoggerLike
from common.utils.backoff import AsyncBackoff


class RedisClient:
    def __init__(self, host: str, port: int, database: int, password: str, logger: LoggerLike) -> None:
        self._host = host
        self._port = port
        self._db = database
        self._logger = logger
        self._client = Redis.from_url(f"redis://:{password}@{host}:{port}/{database}", decode_responses=True)
        self._is_ready = False
        RedisInstrumentor.instrument_client(client=self._client)

    async def start(self) -> None:
        self._logger.info("Connecting to redis at %s:%s to database '%s'...", self._host, self._port, self._db)
        backoff = AsyncBackoff(name="Redis client", logger=self._logger)
        await backoff.run(lambda: self._client.ping())
        self._is_ready = True

    async def stop(self) -> None:
        self._logger.info("Shutting down the redis client...")
        if self._client:
            try:
                await self._client.close()
            finally:
                with suppress(Exception):
                    await self._client.connection_pool.disconnect()
        self._is_ready = False

    async def is_ready(self) -> bool:
        return self._is_ready

    async def is_healthy(self) -> bool:
        if not self._is_ready:
            return False
        return await self._client.ping()

    @property
    def redis(self) -> Redis:
        return self._client
