from aiogram import F, Router
from aiogram.types import CallbackQuery

from src.bot.texts import (
    INSTRUCTION_ANDROID,
    INSTRUCTION_IOS,
    INSTRUCTION_LINUX,
    INSTRUCTION_MACOS,
    INSTRUCTION_PICK_OS,
    INSTRUCTION_WINDOWS,
)

router = Router(name="howto")


_TEXTS = {
    "ios": INSTRUCTION_IOS,
    "android": INSTRUCTION_ANDROID,
    "macos": INSTRUCTION_MACOS,
    "windows": INSTRUCTION_WINDOWS,
    "linux": INSTRUCTION_LINUX,
}


@router.callback_query(F.data == "howto:about")
async def cb_about(call: CallbackQuery) -> None:
    await call.message.answer(
        "У White Crow VPN нет фиксированной подписки.\n\n"
        "Ты платишь только за дни использования: 7 ₽/сутки за одно устройство "
        "или 14 ₽/сутки за пятерых.\n\n"
        "Баланс лежит у тебя на счёте, каждое утро автоматически списывается дневная ставка. "
        "Кончился баланс — VPN отключается. Пополнил — включается снова.",
    )
    await call.answer()


@router.callback_query(F.data.startswith("howto:"))
async def cb_pick(call: CallbackQuery) -> None:
    key = call.data.split(":")[1]
    text = _TEXTS.get(key)
    if text is None:
        await call.message.answer(INSTRUCTION_PICK_OS)
    else:
        await call.message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
    await call.answer()
