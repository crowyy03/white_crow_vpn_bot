from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from src.bot.keyboards import connect_buttons


async def send_subscription_link(
    bot: Bot, telegram_id: int, subscription_url: str, expire_str: str
) -> None:
    text = (
        f"✅ Оплата получена!\n\n"
        f"Подписка активна до: <b>{expire_str}</b>\n\n"
        f"Ваша ссылка:\n<code>{subscription_url}</code>"
    )
    try:
        await bot.send_message(
            telegram_id,
            text,
            reply_markup=connect_buttons(subscription_url),
            parse_mode="HTML",
        )
    except TelegramAPIError as e:
        logger.error("send_subscription_link failed for {}: {}", telegram_id, e)
