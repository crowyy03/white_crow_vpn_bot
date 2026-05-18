from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from src.bot.keyboards import after_topup_actions
from src.bot.texts import TOPUP_SUCCESS, TOPUP_SUCCESS_NO_VPN_YET
from src.services.subscription import TopupResult


async def send_topup_success(bot: Bot, result: TopupResult) -> None:
    rate = result.daily_rate_kopecks
    days = result.new_balance_kopecks // rate if rate else 0
    template = TOPUP_SUCCESS if result.vpn_enabled else TOPUP_SUCCESS_NO_VPN_YET
    try:
        await bot.send_message(
            result.telegram_id,
            template.format(
                amount=result.amount_kopecks // 100,
                days=days,
                plan_name=result.plan_name,
            ),
            reply_markup=after_topup_actions(),
            parse_mode="HTML",
        )
    except TelegramAPIError as e:
        logger.error("send_topup_success failed for {}: {}", result.telegram_id, e)
