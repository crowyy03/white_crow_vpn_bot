from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


PAYMENT_METHOD_LABELS: dict[str, str] = {
    "fake": "🧪 Тестовая оплата (dev)",
    "lava": "💳 Карта РФ · СБП (Lava)",
    "paypalych": "💳 Карта РФ (Paypalych)",
    "yookassa": "💳 YooKassa",
    "cryptomus": "₿ Криптовалюта · USDT / TON / BTC",
    "stars": "⭐ Telegram Stars",
}

TOPUP_AMOUNTS_RUB: tuple[int, ...] = (100, 200, 500, 1000)


def main_menu() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(
        KeyboardButton(text="💳 Пополнить баланс"),
        KeyboardButton(text="👤 Профиль"),
    )
    b.row(
        KeyboardButton(text="🎁 Триал 3 дня"),
        KeyboardButton(text="👥 Рефералка"),
    )
    b.row(
        KeyboardButton(text="📖 Инструкция"),
        KeyboardButton(text="🆘 Поддержка"),
    )
    return b.as_markup(resize_keyboard=True)


def welcome_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🎁 Получить 3 дня бесплатно", callback_data="trial:start"))
    b.row(
        InlineKeyboardButton(text="Как это работает", callback_data="howto:about"),
        InlineKeyboardButton(text="Цены", callback_data="plan:show"),
    )
    return b.as_markup()


def topup_amounts_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    row = [
        InlineKeyboardButton(text=f"{rub} ₽", callback_data=f"topup:amt:{rub}")
        for rub in TOPUP_AMOUNTS_RUB
    ]
    b.row(*row[:2])
    b.row(*row[2:])
    b.row(InlineKeyboardButton(text="✏️ Своя сумма", callback_data="topup:custom"))
    return b.as_markup()


def topup_methods_keyboard(amount_rub: int, methods: list[str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for m in methods:
        b.row(
            InlineKeyboardButton(
                text=PAYMENT_METHOD_LABELS.get(m, m),
                callback_data=f"topup:pay:{m}:{amount_rub}",
            )
        )
    b.row(InlineKeyboardButton(text="« Назад", callback_data="topup:back"))
    return b.as_markup()


def topup_invoice_actions(payment_url: str, order_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="💳 Оплатить", url=payment_url))
    b.row(InlineKeyboardButton(text="🔄 Я оплатил", callback_data=f"topup:check:{order_id}"))
    return b.as_markup()


def plans_keyboard(current_code: str | None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    solo = f"{'● ' if current_code == 'solo' else ''}Solo · 7 ₽/сутки"
    family = f"{'● ' if current_code == 'family' else ''}Family · 14 ₽/сутки"
    b.row(InlineKeyboardButton(text=solo, callback_data="plan:pick:solo"))
    b.row(InlineKeyboardButton(text=family, callback_data="plan:pick:family"))
    return b.as_markup()


def profile_actions(*, has_vpn: bool, current_plan: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup:start"))
    if has_vpn:
        b.row(
            InlineKeyboardButton(text="🔗 Ссылка", callback_data="profile:copy"),
            InlineKeyboardButton(text="📷 QR", callback_data="profile:qr"),
        )
    other = "family" if current_plan == "solo" else "solo"
    other_label = "Family (14 ₽/сутки · 5 устройств)" if other == "family" else "Solo (7 ₽/сутки · 1 устройство)"
    b.row(
        InlineKeyboardButton(
            text=f"Сменить тариф → {other_label}",
            callback_data=f"plan:pick:{other}",
        )
    )
    return b.as_markup()


def disabled_actions() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup:start"))
    return b.as_markup()


def low_balance_quick_topup() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="100 ₽", callback_data="topup:amt:100"),
        InlineKeyboardButton(text="200 ₽", callback_data="topup:amt:200"),
        InlineKeyboardButton(text="500 ₽", callback_data="topup:amt:500"),
    )
    return b.as_markup()


def after_topup_actions() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="💳 Пополнить ещё", callback_data="topup:start"),
        InlineKeyboardButton(text="👤 Профиль", callback_data="profile:show"),
    )
    return b.as_markup()


def os_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="iPhone", callback_data="howto:ios"),
        InlineKeyboardButton(text="iPad", callback_data="howto:ios"),
        InlineKeyboardButton(text="Android", callback_data="howto:android"),
    )
    b.row(
        InlineKeyboardButton(text="macOS", callback_data="howto:macos"),
        InlineKeyboardButton(text="Windows", callback_data="howto:windows"),
        InlineKeyboardButton(text="Linux", callback_data="howto:linux"),
    )
    return b.as_markup()


def connect_buttons(sub_url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="📋 Скопировать ссылку", callback_data="profile:copy"),
        InlineKeyboardButton(text="📷 QR-код", callback_data="profile:qr"),
    )
    b.row(InlineKeyboardButton(text="📖 Инструкция", callback_data="profile:howto"))
    return b.as_markup()
