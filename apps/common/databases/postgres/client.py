from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from common.logs import LoggerLike
from common.utils.backoff import AsyncBackoff


class PostgresClient:
    def __init__(self, user: str, password: str, host: str, port: int, database: str, logger: LoggerLike) -> None:
        self._logger = logger
        self._user = user
        self._host = host
        self._port = port
        self._database = database
        self._is_ready = False
        self._engine = create_async_engine(
            f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}", echo=False, future=True
        )
        SQLAlchemyInstrumentor().instrument(engine=self._engine.sync_engine)
        self._async_session = async_sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)

    async def start(self) -> None:
        self._logger.info(
            "Connecting to postgres on %s:%s to database '%s' using user '%s'...",
            self._host,
            self._port,
            self._database,
            self._user,
        )
        backoff = AsyncBackoff(name="Postgres client", logger=self._logger)
        
        async def check_connection() -> None:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))

        await backoff.run(check_connection)
        self._is_ready = True

    async def stop(self) -> None:
        self._logger.info("Shutting down the postgres client...")
        await self._engine.dispose()
        self._is_ready = False

    async def is_ready(self) -> bool:
        return self._is_ready

    async def is_healthy(self) -> bool:
        if not self._is_ready:
            return False
        async with self._async_session() as session:
            await session.execute(text("SELECT 1"))
        return True

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @property
    def sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        return self._async_session
