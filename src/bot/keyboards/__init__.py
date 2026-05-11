from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from src.db.models import Tariff


PAYMENT_METHOD_LABELS: dict[str, str] = {
    "fake": "🧪 Тестовая оплата (dev)",
    "paypalych": "💳 Картой (Paypalych)",
    "yookassa": "💳 YooKassa",
    "cryptomus": "₿ Cryptomus (USDT)",
    "stars": "⭐ Telegram Stars",
}


def main_menu() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="💳 Купить подписку"))
    b.row(KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="🎁 Пробный период"))
    b.row(KeyboardButton(text="👥 Рефералка"), KeyboardButton(text="📖 Инструкция"))
    b.row(KeyboardButton(text="🆘 Поддержка"))
    return b.as_markup(resize_keyboard=True)


def tariffs_keyboard(tariffs: list[Tariff]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for t in tariffs:
        b.row(
            InlineKeyboardButton(
                text=f"{t.name} — {t.price_kopecks // 100} ₽",
                callback_data=f"buy:tariff:{t.id}",
            )
        )
    b.row(InlineKeyboardButton(text="« Назад", callback_data="buy:cancel"))
    return b.as_markup()


def payment_methods_keyboard(
    tariff_id: int, methods: list[str]
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for m in methods:
        label = PAYMENT_METHOD_LABELS.get(m, m)
        b.row(
            InlineKeyboardButton(
                text=label, callback_data=f"buy:pay:{m}:{tariff_id}"
            )
        )
    b.row(InlineKeyboardButton(text="« Выбрать другой тариф", callback_data="buy:start"))
    return b.as_markup()


def invoice_actions(payment_url: str, order_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="💳 Оплатить", url=payment_url))
    b.row(
        InlineKeyboardButton(
            text="🔄 Я оплатил", callback_data=f"buy:check:{order_id}"
        )
    )
    return b.as_markup()


def connect_buttons(sub_url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="📋 Копировать ссылку", callback_data="profile:copy"),
        InlineKeyboardButton(text="📷 QR-код", callback_data="profile:qr"),
    )
    b.row(InlineKeyboardButton(text="📖 Как подключить", callback_data="profile:howto"))
    return b.as_markup()
