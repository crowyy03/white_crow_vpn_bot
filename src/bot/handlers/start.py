from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import main_menu, welcome_keyboard
from src.bot.texts import WELCOME, WELCOME_RETURN
from src.db.repos import UsersRepo

router = Router(name="start")


def _parse_ref(args: str | None) -> int | None:
    if not args:
        return None
    if args.startswith("ref_"):
        try:
            return int(args[4:])
        except ValueError:
            return None
    return None


@router.message(CommandStart())
async def handle_start(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
) -> None:
    repo = UsersRepo(session)
    referrer_id = _parse_ref(command.args)

    referrer_user_id: int | None = None
    if referrer_id and referrer_id != message.from_user.id:
        existing = await repo.get_by_telegram_id(referrer_id)
        if existing:
            referrer_user_id = existing.id

    _, created = await repo.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        language_code=message.from_user.language_code,
        referrer_id=referrer_user_id,
    )

    name = message.from_user.first_name or message.from_user.username or "друг"
    if created:
        await message.answer(WELCOME, reply_markup=main_menu(), parse_mode="HTML")
        await message.answer(
            "Начнём?", reply_markup=welcome_keyboard()
        )
    else:
        await message.answer(
            WELCOME_RETURN.format(name=name),
            reply_markup=main_menu(),
            parse_mode="HTML",
        )
