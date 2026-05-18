from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import (
    after_topup_actions,
    topup_amounts_keyboard,
    topup_invoice_actions,
    topup_methods_keyboard,
)
from src.bot.states import TopupStates
from src.bot.texts import (
    TOPUP_BAD_AMOUNT,
    TOPUP_CUSTOM_PROMPT,
    TOPUP_FAKE_PAID,
    TOPUP_INVOICE_SENT,
    TOPUP_PICK_AMOUNT,
    TOPUP_PICK_METHOD,
    TOPUP_SUCCESS,
    TOPUP_SUCCESS_NO_VPN_YET,
)
from src.config import get_settings
from src.db.repos import OrdersRepo, UsersRepo
from src.services.payments import FakeProvider, PaymentProvider
from src.services.subscription import process_topup

router = Router(name="topup")


def _plan_name(plan_code: str) -> str:
    return "Solo" if plan_code == "solo" else "Family"


async def show_topup_amounts(message: Message, session: AsyncSession, **_: object) -> None:
    user = await UsersRepo(session).get_by_telegram_id(message.from_user.id)
    plan = user.plan if user else "solo"
    await message.answer(
        TOPUP_PICK_AMOUNT.format(plan_name=_plan_name(plan)),
        reply_markup=topup_amounts_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "topup:start")
async def cb_topup_start(call: CallbackQuery, session: AsyncSession) -> None:
    user = await UsersRepo(session).get_by_telegram_id(call.from_user.id)
    plan = user.plan if user else "solo"
    await call.message.answer(
        TOPUP_PICK_AMOUNT.format(plan_name=_plan_name(plan)),
        reply_markup=topup_amounts_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "topup:back")
async def cb_topup_back(call: CallbackQuery, session: AsyncSession) -> None:
    user = await UsersRepo(session).get_by_telegram_id(call.from_user.id)
    plan = user.plan if user else "solo"
    await call.message.edit_text(
        TOPUP_PICK_AMOUNT.format(plan_name=_plan_name(plan)),
        reply_markup=topup_amounts_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "topup:custom")
async def cb_custom_amount(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TopupStates.waiting_custom_amount)
    await call.message.answer(TOPUP_CUSTOM_PROMPT)
    await call.answer()


@router.message(StateFilter(TopupStates.waiting_custom_amount))
async def on_custom_amount(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    settings = get_settings()
    text = (message.text or "").strip().replace(" ", "")
    try:
        amount_rub = int(text)
    except ValueError:
        await message.answer(TOPUP_BAD_AMOUNT)
        return

    amount_kopecks = amount_rub * 100
    if (
        amount_kopecks < settings.topup_min_kopecks
        or amount_kopecks > settings.topup_max_kopecks
    ):
        await message.answer(TOPUP_BAD_AMOUNT)
        return

    await state.clear()
    methods = settings.available_payment_methods
    if not methods:
        await message.answer("Платёжные методы пока не настроены.")
        return

    await message.answer(
        TOPUP_PICK_METHOD.format(amount=amount_rub),
        reply_markup=topup_methods_keyboard(amount_rub, methods),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("topup:amt:"))
async def cb_pick_amount(call: CallbackQuery) -> None:
    amount_rub = int(call.data.split(":")[2])
    settings = get_settings()
    methods = settings.available_payment_methods
    if not methods:
        await call.answer("Платёжные методы пока не настроены.", show_alert=True)
        return
    await call.message.edit_text(
        TOPUP_PICK_METHOD.format(amount=amount_rub),
        reply_markup=topup_methods_keyboard(amount_rub, methods),
        parse_mode="HTML",
    )
    await call.answer()


def _provider(method: str) -> PaymentProvider | None:
    if method == "fake":
        return FakeProvider()
    if method == "cryptomus":
        from src.services.payments.cryptomus import CryptomusProvider

        return CryptomusProvider()
    if method == "yookassa":
        from src.services.payments.yookassa import YookassaProvider

        return YookassaProvider()
    if method == "paypalych":
        from src.services.payments.paypalych import PaypalychProvider

        return PaypalychProvider()
    if method == "lava":
        from src.services.payments.lava import LavaProvider

        return LavaProvider()
    return None


@router.callback_query(F.data.startswith("topup:pay:"))
async def cb_pay(call: CallbackQuery, session: AsyncSession) -> None:
    _, _, method, amount_rub_s = call.data.split(":")
    amount_rub = int(amount_rub_s)
    amount_kopecks = amount_rub * 100

    settings = get_settings()
    if method not in settings.available_payment_methods:
        await call.answer("Этот способ оплаты пока не доступен", show_alert=True)
        return

    user = await UsersRepo(session).get_by_telegram_id(call.from_user.id)
    if user is None:
        await call.answer("Сначала нажми /start", show_alert=True)
        return

    if method == "stars":
        await _pay_with_stars(call, session, user.id, amount_kopecks)
        return

    provider = _provider(method)
    if provider is None:
        await call.answer("Этот способ оплаты пока не доступен", show_alert=True)
        return

    orders = OrdersRepo(session)
    order = await orders.create_topup(
        user_id=user.id,
        amount_kopecks=amount_kopecks,
        payment_method=method,
    )

    try:
        result = await provider.create_invoice(
            order_id=order.id,
            amount_kopecks=amount_kopecks,
            description=f"Пополнение баланса White Crow VPN — {amount_rub} ₽",
        )
    except Exception as e:
        logger.exception("create_invoice failed: {}", e)
        await call.answer("Не получилось создать счёт. Попробуй позже.", show_alert=True)
        return

    await orders.set_payment_info(order.id, result.payment_url, result.external_id)

    await call.message.edit_text(
        TOPUP_INVOICE_SENT.format(amount=amount_rub),
        reply_markup=topup_invoice_actions(result.payment_url, order.id),
        parse_mode="HTML",
    )
    await call.answer()


async def _pay_with_stars(
    call: CallbackQuery, session: AsyncSession, user_id: int, amount_kopecks: int
) -> None:
    settings = get_settings()
    stars = max(1, amount_kopecks // settings.stars_kopecks_per_star)

    orders = OrdersRepo(session)
    order = await orders.create_topup(
        user_id=user_id,
        amount_kopecks=amount_kopecks,
        payment_method="stars",
    )
    await session.commit()

    await call.message.answer_invoice(
        title="White Crow VPN: пополнение баланса",
        description=f"Пополнение баланса на {amount_kopecks // 100} ₽",
        payload=f"topup_{order.id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"{amount_kopecks // 100} ₽", amount=stars)],
    )
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()


@router.callback_query(F.data.startswith("topup:check:"))
async def cb_check(call: CallbackQuery, session: AsyncSession) -> None:
    order_id = int(call.data.split(":")[2])
    order = await OrdersRepo(session).get(order_id)
    if order is None:
        await call.answer("Заказ не найден", show_alert=True)
        return

    if order.payment_method == "fake":
        result = await process_topup(session, order_id)
        if result is None:
            await call.answer("Уже зачислено или ошибка", show_alert=True)
            return
        await call.message.edit_text(TOPUP_FAKE_PAID)
        await _send_topup_success(call.message, result)
        await call.answer()
        return

    if order.status == "paid":
        await call.answer("Платёж уже зачислен", show_alert=True)
        return

    await call.answer(
        "Платёж ещё не подтверждён. Подожди минуту после оплаты.", show_alert=True
    )


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message, session: AsyncSession) -> None:
    sp = message.successful_payment
    payload = sp.invoice_payload or ""
    if not payload.startswith("topup_"):
        logger.warning("successful_payment: unexpected payload {!r}", payload)
        return
    try:
        order_id = int(payload.removeprefix("topup_"))
    except ValueError:
        logger.warning("successful_payment: bad order_id in payload {!r}", payload)
        return

    await OrdersRepo(session).set_external_id(order_id, sp.telegram_payment_charge_id)
    result = await process_topup(session, order_id)
    if result is None:
        return
    await _send_topup_success(message, result)


async def _send_topup_success(message: Message, result) -> None:
    rate = result.daily_rate_kopecks
    days = result.new_balance_kopecks // rate if rate else 0
    template = TOPUP_SUCCESS if result.vpn_enabled else TOPUP_SUCCESS_NO_VPN_YET
    await message.answer(
        template.format(
            amount=result.amount_kopecks // 100,
            days=days,
            plan_name=result.plan_name,
        ),
        reply_markup=after_topup_actions(),
        parse_mode="HTML",
    )
