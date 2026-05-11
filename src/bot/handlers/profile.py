import io
from datetime import datetime, timezone

import qrcode
from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import connect_buttons
from src.bot.texts import INSTRUCTION, PROFILE_ACTIVE, PROFILE_NO_SUB
from src.db.repos import UsersRepo

router = Router(name="profile")


async def show_profile(message: Message, session: AsyncSession, **_: object) -> None:
    user = await UsersRepo(session).get_by_telegram_id(message.from_user.id)
    if user is None or not user.subscription_until or not user.subscription_url:
        await message.answer(PROFILE_NO_SUB)
        return

    now = datetime.now(timezone.utc)
    if user.subscription_until < now:
        await message.answer(PROFILE_NO_SUB)
        return

    days_left = max(0, (user.subscription_until - now).days)
    await message.answer(
        PROFILE_ACTIVE.format(
            until=user.subscription_until.strftime("%d.%m.%Y"),
            days_left=days_left,
            sub_url=user.subscription_url,
        ),
        reply_markup=connect_buttons(user.subscription_url),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "profile:copy")
async def on_copy(call: CallbackQuery, session: AsyncSession) -> None:
    user = await UsersRepo(session).get_by_telegram_id(call.from_user.id)
    if user is None or not user.subscription_url:
        await call.answer("Сначала купи или активируй подписку", show_alert=True)
        return
    await call.message.answer(
        f"<code>{user.subscription_url}</code>\n\nНажми на ссылку выше, чтобы скопировать.",
        parse_mode="HTML",
    )
    await call.answer("Ссылка отправлена")


@router.callback_query(F.data == "profile:qr")
async def on_qr(call: CallbackQuery, session: AsyncSession) -> None:
    user = await UsersRepo(session).get_by_telegram_id(call.from_user.id)
    if user is None or not user.subscription_url:
        await call.answer("Сначала купи или активируй подписку", show_alert=True)
        return
    img = qrcode.make(user.subscription_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    await call.message.answer_photo(
        BufferedInputFile(buf.read(), filename="subscription.png"),
        caption="QR-код подписки. Отсканируй в Happ/v2rayNG/Streisand.",
    )
    await call.answer()


@router.callback_query(F.data == "profile:howto")
async def on_howto(call: CallbackQuery) -> None:
    await call.message.answer(INSTRUCTION, parse_mode="HTML", disable_web_page_preview=True)
    await call.answer()
