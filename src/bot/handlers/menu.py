from aiogram import F, Router
from aiogram.types import Message

from src.bot.handlers.profile import show_profile
from src.bot.handlers.referral import show_referral
from src.bot.handlers.topup import show_topup_amounts
from src.bot.handlers.trial import grant_trial
from src.bot.keyboards import os_keyboard
from src.bot.texts import INSTRUCTION_PICK_OS, SUPPORT
from src.config import get_settings

router = Router(name="menu")


@router.message(F.text == "💳 Пополнить баланс")
async def on_topup(message: Message, **data) -> None:
    await show_topup_amounts(message, **data)


@router.message(F.text == "👤 Профиль")
async def on_profile(message: Message, **data) -> None:
    await show_profile(message, **data)


@router.message(F.text == "🎁 Триал 3 дня")
async def on_trial(message: Message, **data) -> None:
    await grant_trial(message, **data)


@router.message(F.text == "👥 Рефералка")
async def on_referral(message: Message, **data) -> None:
    await show_referral(message, **data)


@router.message(F.text == "📖 Инструкция")
async def on_instruction(message: Message) -> None:
    await message.answer(INSTRUCTION_PICK_OS, reply_markup=os_keyboard())


@router.message(F.text == "🆘 Поддержка")
async def on_support(message: Message) -> None:
    await message.answer(SUPPORT.format(username=get_settings().support_username))
