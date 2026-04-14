from argparse import ArgumentParser, Namespace
import asyncio
import logging
from pathlib import Path
from typing import Any

from aiohttp import ClientSession


class PulseHubAPI:
    def __init__(self, base_url: str, logger: logging.Logger) -> None:
        self._session = ClientSession()
        self._base_url = base_url
        self._logger = logger

    async def stop(self) -> None:
        await self._session.close()

    async def create(self, url: str) -> None:
        self._logger.info("Making POST request to /targets with '%s'...", url)
        async with self._session.post(f"{self._base_url}/targets", json={"targetUrl": url}) as response:
            response.raise_for_status()

    async def delete(self, target_id: str) -> None:
        self._logger.info("Making DELETE request to /targets/%s...", target_id)
        await self._session.delete(f"{self._base_url}/targets/{target_id}")

    async def get(self, target_id: str) -> dict[str, Any]:
        self._logger.info("Making GET request to /targets/%s...", target_id)
        response = await self._session.get(f"{self._base_url}/targets/{target_id}")
        target = await response.json()
        return target

    async def list(self) -> list[dict[str, Any]]:
        self._logger.info("Making GET request to /targets...")
        response = await self._session.get(f"{self._base_url}/targets")
        targets = await response.json()
        return targets["targets"]


class Bootstrap:
    TARGETS_FILE_PATH = Path(__file__).resolve().parent / "targets.txt"

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._args = self._load_arguments()
        self._targets = self._load_targets()

    def _load_arguments(self) -> Namespace:
        parser = ArgumentParser()
        parser.add_argument("endpoint")
        args = parser.parse_args()
        self._logger.info("Got command line arguments: ", args)
        return args

    def _load_targets(self) -> list[str]:
        with open(self.TARGETS_FILE_PATH, encoding="utf-8", mode="r") as file:
            result = [line.strip() for line in file.readlines()]
        self._logger.info("Loaded %s targets from '%s'", len(result), self.TARGETS_FILE_PATH)
        return result

    @property
    def targets(self) -> list[str]:
        return self._targets

    @property
    def server_url(self) -> str:
        return self._args.endpoint


class StressTest:
    def __init__(self, api: PulseHubAPI, targets: list[str], logger: logging.Logger) -> None:
        self._api = api
        self._targets = targets
        self._logger = logger

    async def create_targets(self) -> None:
        self._logger.info("Creating %s targets...", len(self._targets))
        for target in self._targets:
            await self._api.create(target)

    async def imitate_load(self) -> None:
        while True:
            await self._api.list()
            await asyncio.sleep(0.5)

    async def __aenter__(self):
        self._logger.info("Starting stress test")
        return self

    async def end(self) -> None:
        await self._api.stop()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._logger.info("Ending test...")
        await self._api.stop()
        if exc_type:
            self._logger.error(f"Error during stress test: {exc_val}")



async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s]: %(message)s")
    logger = logging.getLogger(__name__)
    bootstrap = Bootstrap(logger=logger)
    api = PulseHubAPI(base_url=bootstrap.server_url, logger=logger)

    async with StressTest(api, targets=bootstrap.targets, logger=logger) as test:
        await test.create_targets()
        await test.imitate_load()



if __name__ == "__main__":
    asyncio.run(main())
