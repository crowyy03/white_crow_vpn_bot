from aiogram import F, Router
from aiogram.types import Message

from src.bot.handlers.buy import show_tariffs
from src.bot.handlers.profile import show_profile
from src.bot.handlers.referral import show_referral
from src.bot.handlers.trial import grant_trial
from src.bot.texts import INSTRUCTION, SUPPORT
from src.config import get_settings

router = Router(name="menu")


@router.message(F.text == "💳 Купить подписку")
async def on_buy(message: Message, **data) -> None:
    await show_tariffs(message, **data)


@router.message(F.text == "👤 Мой профиль")
async def on_profile(message: Message, **data) -> None:
    await show_profile(message, **data)


@router.message(F.text == "🎁 Пробный период")
async def on_trial(message: Message, **data) -> None:
    await grant_trial(message, **data)


@router.message(F.text == "👥 Рефералка")
async def on_referral(message: Message, **data) -> None:
    await show_referral(message, **data)


@router.message(F.text == "📖 Инструкция")
async def on_instruction(message: Message) -> None:
    await message.answer(INSTRUCTION, parse_mode="HTML", disable_web_page_preview=True)


@router.message(F.text == "🆘 Поддержка")
async def on_support(message: Message) -> None:
    await message.answer(SUPPORT.format(username=get_settings().support_username))
