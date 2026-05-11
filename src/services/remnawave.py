from dataclasses import dataclass
from datetime import datetime

import httpx
from loguru import logger

from src.config import get_settings


@dataclass
class RemnawaveUser:
    uuid: str
    short_uuid: str
    subscription_url: str
    expire_at: datetime | None


class RemnawaveClient:
    def __init__(self, base_url: str, token: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _client(self) -> httpx.AsyncClient:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout,
        )

    async def create_user(
        self,
        *,
        username: str,
        expire_at: datetime,
        traffic_limit_bytes: int | None,
        squad_uuid: str,
        description: str = "",
    ) -> RemnawaveUser:
        body = {
            "username": username,
            "trafficLimitBytes": traffic_limit_bytes or 0,
            "trafficLimitStrategy": "NO_RESET",
            "expireAt": expire_at.isoformat(),
            "activeInternalSquads": [squad_uuid] if squad_uuid else [],
            "hwidDeviceLimit": 3,
            "description": description,
        }
        async with self._client() as c:
            resp = await c.post("/api/users", json=body)
            resp.raise_for_status()
            data = resp.json()
        return RemnawaveUser(
            uuid=data["uuid"],
            short_uuid=data.get("shortUuid", ""),
            subscription_url=data.get("subscriptionUrl", ""),
            expire_at=expire_at,
        )

    async def update_user_expire(self, uuid: str, expire_at: datetime) -> None:
        async with self._client() as c:
            resp = await c.patch(
                "/api/users",
                json={"uuid": uuid, "expireAt": expire_at.isoformat()},
            )
            resp.raise_for_status()

    async def disable_user(self, uuid: str) -> None:
        async with self._client() as c:
            resp = await c.post(f"/api/users/{uuid}/actions/disable")
            resp.raise_for_status()

    async def enable_user(self, uuid: str) -> None:
        async with self._client() as c:
            resp = await c.post(f"/api/users/{uuid}/actions/enable")
            resp.raise_for_status()


class FakeRemnawaveClient:
    async def create_user(
        self,
        *,
        username: str,
        expire_at: datetime,
        traffic_limit_bytes: int | None,
        squad_uuid: str,
        description: str = "",
    ) -> RemnawaveUser:
        from uuid import uuid4

        uid = uuid4()
        short = uid.hex[:16]
        logger.info("FakeRemnawave: create user {} until {}", username, expire_at)
        return RemnawaveUser(
            uuid=str(uid),
            short_uuid=short,
            subscription_url=f"https://sub.example.com/{short}",
            expire_at=expire_at,
        )

    async def update_user_expire(self, uuid: str, expire_at: datetime) -> None:
        logger.info("FakeRemnawave: extend {} until {}", uuid, expire_at)

    async def disable_user(self, uuid: str) -> None:
        logger.info("FakeRemnawave: disable {}", uuid)

    async def enable_user(self, uuid: str) -> None:
        logger.info("FakeRemnawave: enable {}", uuid)


def make_remnawave_client() -> RemnawaveClient | FakeRemnawaveClient:
    s = get_settings()
    if not s.remnawave_api_token:
        return FakeRemnawaveClient()
    return RemnawaveClient(s.remnawave_api_url, s.remnawave_api_token)
