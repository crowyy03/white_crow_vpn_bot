from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User


class UsersRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        language_code: str | None,
        referrer_id: int | None = None,
    ) -> tuple[User, bool]:
        user = await self.get_by_telegram_id(telegram_id)
        if user is not None:
            return user, False

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language_code=language_code or "ru",
            referrer_id=referrer_id,
        )
        self.session.add(user)
        await self.session.flush()
        return user, True

    async def set_subscription(
        self,
        user_id: int,
        *,
        remnawave_uuid: str | None = None,
        remnawave_short_uuid: str | None = None,
        subscription_url: str | None = None,
        subscription_until: datetime | None = None,
    ) -> None:
        values: dict = {}
        if remnawave_uuid is not None:
            values["remnawave_uuid"] = remnawave_uuid
        if remnawave_short_uuid is not None:
            values["remnawave_short_uuid"] = remnawave_short_uuid
        if subscription_url is not None:
            values["subscription_url"] = subscription_url
        if subscription_until is not None:
            values["subscription_until"] = subscription_until
        if not values:
            return
        await self.session.execute(
            update(User).where(User.id == user_id).values(**values)
        )

    async def mark_trial_used(self, user_id: int) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(trial_used=True)
        )

    async def add_balance(self, user_id: int, delta_kopecks: int) -> None:
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(balance_kopecks=User.balance_kopecks + delta_kopecks)
        )
