from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import (
    connect_buttons,
    invoice_actions,
    payment_methods_keyboard,
    tariffs_keyboard,
)
from src.bot.texts import (
    BUY_FAKE_PAID,
    BUY_INVOICE_SENT,
    BUY_PICK_METHOD,
    BUY_PICK_TARIFF,
    PAY_SUCCESS,
)
from src.config import get_settings
from src.db.repos import OrdersRepo, TariffsRepo, UsersRepo
from src.db.models import Tariff, User
from src.services.payments import FakeProvider, PaymentProvider
from src.services.subscription import process_payment

router = Router(name="buy")


async def show_tariffs(message: Message, session: AsyncSession, **_: object) -> None:
    tariffs = await TariffsRepo(session).list_active()
    await message.answer(BUY_PICK_TARIFF, reply_markup=tariffs_keyboard(tariffs))


@router.callback_query(F.data == "buy:start")
async def cb_start(call: CallbackQuery, session: AsyncSession) -> None:
    tariffs = await TariffsRepo(session).list_active()
    await call.message.edit_text(BUY_PICK_TARIFF, reply_markup=tariffs_keyboard(tariffs))
    await call.answer()


@router.callback_query(F.data == "buy:cancel")
async def cb_cancel(call: CallbackQuery) -> None:
    await call.message.delete()
    await call.answer()


@router.callback_query(F.data.startswith("buy:tariff:"))
async def cb_pick_tariff(call: CallbackQuery, session: AsyncSession) -> None:
    tariff_id = int(call.data.split(":")[2])
    tariff = await TariffsRepo(session).get(tariff_id)
    if tariff is None:
        await call.answer("Тариф не найден", show_alert=True)
        return
    settings = get_settings()
    methods = settings.available_payment_methods
    if not methods:
        await call.answer(
            "Платёжные методы пока не настроены администратором.", show_alert=True
        )
        return
    text = BUY_PICK_METHOD.format(tariff=tariff.name, price=tariff.price_kopecks // 100)
    await call.message.edit_text(
        text,
        reply_markup=payment_methods_keyboard(tariff_id, methods),
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
    return None


@router.callback_query(F.data.startswith("buy:pay:"))
async def cb_pay(call: CallbackQuery, session: AsyncSession) -> None:
    _, _, method, tariff_id_s = call.data.split(":")
    tariff_id = int(tariff_id_s)

    tariff = await TariffsRepo(session).get(tariff_id)
    if tariff is None:
        await call.answer("Тариф не найден", show_alert=True)
        return

    user = await UsersRepo(session).get_by_telegram_id(call.from_user.id)
    if user is None:
        await call.answer("Сначала нажми /start", show_alert=True)
        return

    if method not in get_settings().available_payment_methods:
        await call.answer("Этот способ оплаты пока не доступен", show_alert=True)
        return

    if method == "stars":
        await _pay_with_stars(call, session, user, tariff)
        return

    provider = _provider(method)
    if provider is None:
        await call.answer("Этот способ оплаты пока не доступен", show_alert=True)
        return

    orders = OrdersRepo(session)
    order = await orders.create(
        user_id=user.id,
        tariff_id=tariff.id,
        amount_kopecks=tariff.price_kopecks,
        payment_method=method,
    )

    try:
        result = await provider.create_invoice(
            order_id=order.id,
            amount_kopecks=tariff.price_kopecks,
            description=f"VPN {tariff.name}",
        )
    except Exception as e:
        logger.exception("create_invoice failed: {}", e)
        await call.answer("Не получилось создать счёт. Попробуй позже.", show_alert=True)
        return

    await orders.set_payment_info(order.id, result.payment_url, result.external_id)

    await call.message.edit_text(
        BUY_INVOICE_SENT,
        reply_markup=invoice_actions(result.payment_url, order.id),
    )
    await call.answer()


async def _pay_with_stars(
    call: CallbackQuery,
    session: AsyncSession,
    user: User,
    tariff: Tariff,
) -> None:
    if not tariff.price_stars:
        await call.answer("Этот тариф нельзя оплатить через Stars", show_alert=True)
        return

    orders = OrdersRepo(session)
    order = await orders.create(
        user_id=user.id,
        tariff_id=tariff.id,
        amount_kopecks=tariff.price_kopecks,
        payment_method="stars",
    )
    await session.commit()

    await call.message.answer_invoice(
        title=f"VPN: {tariff.name}",
        description=f"Подписка на {tariff.duration_days} дн.",
        payload=f"order_{order.id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=tariff.name, amount=tariff.price_stars)],
    )
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message, session: AsyncSession) -> None:
    sp = message.successful_payment
    payload = sp.invoice_payload or ""
    if not payload.startswith("order_"):
        logger.warning("successful_payment: unexpected payload {!r}", payload)
        return
    try:
        order_id = int(payload.removeprefix("order_"))
    except ValueError:
        logger.warning("successful_payment: bad order_id in payload {!r}", payload)
        return

    orders = OrdersRepo(session)
    await orders.set_external_id(order_id, sp.telegram_payment_charge_id)

    result = await process_payment(session, order_id)
    if result is None:
        return
    _, new_expire = result

    user = await UsersRepo(session).get_by_telegram_id(message.from_user.id)
    if user is None or not user.subscription_url:
        return

    await message.answer(
        PAY_SUCCESS.format(
            until=new_expire.strftime("%d.%m.%Y"),
            sub_url=user.subscription_url,
        ),
        reply_markup=connect_buttons(user.subscription_url),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("buy:check:"))
async def cb_check(call: CallbackQuery, session: AsyncSession) -> None:
    order_id = int(call.data.split(":")[2])
    orders = OrdersRepo(session)
    order = await orders.get(order_id)
    if order is None:
        await call.answer("Заказ не найден", show_alert=True)
        return

    if order.payment_method == "fake":
        result = await process_payment(session, order_id)
        if result is None:
            await call.answer("Уже выдано или ошибка", show_alert=True)
            return
        telegram_id, new_expire = result
        user = await UsersRepo(session).get_by_id(order.user_id)
        await call.message.edit_text(BUY_FAKE_PAID)
        await call.message.answer(
            PAY_SUCCESS.format(
                until=new_expire.strftime("%d.%m.%Y"),
                sub_url=user.subscription_url,
            ),
            reply_markup=connect_buttons(user.subscription_url),
            parse_mode="HTML",
        )
        await call.answer()
        return

    if order.status == "paid":
        await call.answer("Оплата уже зачислена", show_alert=True)
        return

    await call.answer(
        "Платёж ещё не подтверждён. Подожди минуту после оплаты.",
        show_alert=True,
    )
