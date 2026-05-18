WELCOME = (
    "Привет, ты в White Crow VPN.\n\n"
    "Здесь нет подписки. Есть баланс и дневная ставка — "
    "<b>7 ₽/сутки</b> за одно устройство.\n\n"
    "Можно начать с триала — 3 дня без оплаты."
)

WELCOME_RETURN = "С возвращением, <b>{name}</b>."

PROFILE_NO_VPN = (
    "У тебя пока нет VPN-доступа.\n\n"
    "Активируй триал на 3 дня или пополни баланс — VPN включится автоматически."
)

PROFILE_TRIAL = (
    "🎁 <b>Триал активен</b>\n"
    "До <b>{until}</b> — 1 устройство, безлимитный трафик.\n\n"
    "Когда триал закончится — пополни баланс, и VPN продолжит работать.\n"
    "Тариф после триала: <b>{plan_name}</b> · {rate} ₽/сутки"
)

PROFILE_ACTIVE = (
    "● <b>Активен</b>\n"
    "VPN работает.\n\n"
    "Баланс       <b>{balance} ₽</b>\n"
    "Хватит на    <b>{days} дн.</b>\n"
    "Списание     <b>{rate} ₽/сутки</b>\n"
    "Тариф        <b>{plan_name} · {devices}</b>\n\n"
    "Следующее списание сегодня в 00:00 МСК."
)

PROFILE_LOW_BALANCE = (
    "⚠️ <b>Баланс кончается</b>\n"
    "VPN ещё работает, но осталось ~<b>{days} дн.</b>\n\n"
    "Баланс       <b>{balance} ₽</b>\n"
    "Списание     <b>{rate} ₽/сутки</b>\n"
    "Тариф        <b>{plan_name} · {devices}</b>\n\n"
    "Пополни сейчас — и не прервёшься."
)

PROFILE_DISABLED = (
    "❌ <b>VPN отключён</b>\n"
    "Баланс кончился. Положи любую сумму от 100 ₽ — включится автоматически.\n\n"
    "Тариф        <b>{plan_name} · {devices}</b>"
)

PLAN_DESC_SOLO = "Solo · 1 устройство"
PLAN_DESC_FAMILY = "Family · 5 устройств"

PLAN_PICK = (
    "Выбери тариф.\n\n"
    "<b>Solo</b> — 1 устройство, 7 ₽/сутки\n"
    "<b>Family</b> — до 5 устройств, 14 ₽/сутки\n\n"
    "Сменить тариф можно в любой момент. "
    "Списание начнётся со следующих суток."
)
PLAN_SWITCHED = "✅ Тариф сменён на <b>{plan_name}</b>."
PLAN_SAME = "Этот тариф уже выбран."

TOPUP_PICK_AMOUNT = (
    "Сколько положить?\n"
    "Минимум 100 ₽. <b>{plan_name}</b>.\n"
    "Баланс не сгорает — лежит у тебя на счёте до использования."
)

TOPUP_PICK_METHOD = (
    "К пополнению: <b>{amount} ₽</b>\n\n"
    "Как удобнее заплатить?"
)

TOPUP_CUSTOM_PROMPT = (
    "Введи сумму в рублях. От 100 до 50 000."
)

TOPUP_BAD_AMOUNT = "Сумма должна быть целым числом от 100 до 50 000."

TOPUP_INVOICE_SENT = (
    "Счёт на <b>{amount} ₽</b> создан. "
    "Нажми «Оплатить» — после оплаты баланс пополнится автоматически."
)

TOPUP_FAKE_PAID = "✅ Тестовая оплата принята (фейк)."

TOPUP_SUCCESS = (
    "✅ <b>Баланс пополнен на {amount} ₽</b>\n"
    "VPN снова активен. Хватит на <b>{days} дн.</b> {plan_name}."
)

TOPUP_SUCCESS_NO_VPN_YET = (
    "✅ <b>Баланс пополнен на {amount} ₽</b>\n"
    "Хватит на <b>{days} дн.</b> {plan_name}.\n\n"
    "Подключение готово."
)

LOW_BALANCE_NOTIFICATION = (
    "⚠️ <b>Осталось ~{days} дн.</b>\n"
    "На балансе {balance} ₽. {plan_name}.\n"
    "Пополни сейчас — и не прервёшься."
)

VPN_DISABLED_NOTIFICATION = (
    "❌ <b>VPN отключён</b>\n"
    "Баланс кончился. Положи любую сумму от 100 ₽ — включится автоматически."
)

VPN_RESTORED_NOTIFICATION = (
    "✅ <b>VPN снова активен</b>\n"
    "Хватит на ~{days} дн. {plan_name}."
)

TRIAL_USED = "Бесплатный триал уже был использован."
TRIAL_GRANTED = (
    "🎁 Триал активирован.\n"
    "До <b>{until}</b> — 1 устройство, безлимитный трафик.\n\n"
    "<code>{sub_url}</code>"
)

REFERRAL_INFO = (
    "👥 <b>Реферальная программа</b>\n\n"
    "Твоя ссылка:\n<code>{link}</code>\n\n"
    "Приглашено: <b>{count}</b>\n"
    "Баланс: <b>{balance} ₽</b>\n\n"
    "Получай {percent}% с каждого пополнения приглашённого друга."
)

SUPPORT = "По всем вопросам пиши: {username}"

INSTRUCTION_PICK_OS = (
    "Выбери устройство.\n"
    "Я открою клиент в один тап — настраивать руками ничего не придётся."
)

INSTRUCTION_IOS = (
    "📱 <b>iPhone / iPad</b>\n\n"
    "1. Установи <b>Happ</b> из App Store.\n"
    "2. Открой ссылку подписки — она автоматически добавится в клиент.\n"
    "3. Включи переключатель и пользуйся.\n\n"
    "Скачать: https://apps.apple.com/app/happ/id6504287215"
)

INSTRUCTION_ANDROID = (
    "🤖 <b>Android</b>\n\n"
    "1. Установи <b>Happ</b> из Google Play.\n"
    "2. Открой ссылку подписки — клиент подхватит её сам.\n"
    "3. Нажми Connect.\n\n"
    "Скачать: https://play.google.com/store/apps/details?id=com.happproxy"
)

INSTRUCTION_MACOS = (
    "🍎 <b>macOS</b>\n\n"
    "1. Установи <b>Happ</b> или <b>V2RayU</b>.\n"
    "2. Импортируй подписку по ссылке из профиля.\n"
    "3. Включи системный прокси."
)

INSTRUCTION_WINDOWS = (
    "🪟 <b>Windows</b>\n\n"
    "1. Скачай <b>v2rayN</b>: https://github.com/2dust/v2rayN/releases\n"
    "2. Добавь подписку: <i>Subscription → Add subscription</i>.\n"
    "3. Обнови подписку и подключайся."
)

INSTRUCTION_LINUX = (
    "🐧 <b>Linux</b>\n\n"
    "1. Установи <b>v2rayA</b> или <b>nekoray</b>.\n"
    "2. Добавь ссылку подписки.\n"
    "3. Подключайся."
)

ADMIN_ONLY = "Команда доступна только администратору."
