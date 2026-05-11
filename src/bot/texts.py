WELCOME = (
    "👋 Привет, <b>{name}</b>!\n\n"
    "Это бот для покупки VPN-доступа. Безлимит, быстрые серверы, мгновенная "
    "автовыдача конфига после оплаты.\n\n"
    "Выбирай в меню ниже 👇"
)

WELCOME_RETURN = "С возвращением, <b>{name}</b>! 👋"

PROFILE_NO_SUB = "У тебя пока нет активной подписки. Жми «💳 Купить подписку»."
PROFILE_ACTIVE = (
    "👤 <b>Профиль</b>\n\n"
    "Подписка до: <b>{until}</b>\n"
    "Осталось: <b>{days_left}</b> дн.\n\n"
    "Ссылка:\n<code>{sub_url}</code>"
)

BUY_PICK_TARIFF = "Выбери тариф:"
BUY_PICK_METHOD = "Тариф: <b>{tariff}</b>\nСумма: <b>{price} ₽</b>\n\nВыбери способ оплаты:"
BUY_INVOICE_SENT = (
    "Счёт создан. Нажми «Оплатить», после оплаты подписка появится "
    "автоматически в течение минуты."
)
BUY_FAKE_PAID = "✅ Тестовая оплата принята (фейк-провайдер)."

PAY_SUCCESS = (
    "✅ Оплата получена!\n\n"
    "Подписка активна до: <b>{until}</b>\n\n"
    "Ваша ссылка:\n<code>{sub_url}</code>"
)

TRIAL_USED = "Бесплатный пробный период уже был использован."
TRIAL_GRANTED = "🎁 Пробный период активирован на {days} дней."

REFERRAL_INFO = (
    "👥 <b>Реферальная программа</b>\n\n"
    "Твоя ссылка:\n<code>{link}</code>\n\n"
    "Приглашено: <b>{count}</b>\n"
    "Баланс: <b>{balance} ₽</b>\n\n"
    "Получай {percent}% с каждой оплаты приглашённого друга."
)

SUPPORT = "По всем вопросам пиши: {username}"

INSTRUCTION = (
    "📖 <b>Как подключиться</b>\n\n"
    "1. Скопируй ссылку из профиля или нажми кнопку клиента ниже.\n"
    "2. Открой её в клиенте: Happ (iOS/Android/macOS), v2rayNG (Android), "
    "v2rayN (Windows), Streisand (iOS).\n"
    "3. Выбери любой сервер и подключайся.\n\n"
    "Скачать клиенты:\n"
    "• iOS: https://apps.apple.com/app/happ/id6504287215\n"
    "• Android: https://play.google.com/store/apps/details?id=com.happproxy\n"
    "• Windows: https://github.com/2dust/v2rayN/releases"
)

ADMIN_ONLY = "Команда доступна только администратору."
