from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import plans_keyboard
from src.bot.texts import PLAN_PICK, PLAN_SAME, PLAN_SWITCHED
from src.db.repos import TariffsRepo, UsersRepo

router = Router(name="plan")


async def show_plans(message: Message, session: AsyncSession, **_: object) -> None:
    user = await UsersRepo(session).get_by_telegram_id(message.from_user.id)
    current = user.plan if user else None
    await message.answer(PLAN_PICK, reply_markup=plans_keyboard(current), parse_mode="HTML")


@router.callback_query(F.data == "plan:show")
async def cb_show(call: CallbackQuery, session: AsyncSession) -> None:
    user = await UsersRepo(session).get_by_telegram_id(call.from_user.id)
    current = user.plan if user else None
    await call.message.answer(PLAN_PICK, reply_markup=plans_keyboard(current), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("plan:pick:"))
async def cb_pick(call: CallbackQuery, session: AsyncSession) -> None:
    code = call.data.split(":")[2]
    if code not in ("solo", "family"):
        await call.answer("Неизвестный тариф", show_alert=True)
        return

    users = UsersRepo(session)
    user = await users.get_by_telegram_id(call.from_user.id)
    if user is None:
        await call.answer("Сначала нажми /start", show_alert=True)
        return

    if user.plan == code:
        await call.answer(PLAN_SAME, show_alert=True)
        return

    tariff = await TariffsRepo(session).get_by_code(code)
    if tariff is None:
        await call.answer("Тариф не найден", show_alert=True)
        return

    await users.set_plan(user.id, code)
    await call.message.answer(
        PLAN_SWITCHED.format(plan_name=tariff.name), parse_mode="HTML"
    )
    await call.answer()
