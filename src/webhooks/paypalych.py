from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from src.db.repos import OrdersRepo, UsersRepo
from src.services.notifications import send_subscription_link
from src.services.payments.paypalych import verify_postback_signature
from src.services.subscription import process_payment

router = APIRouter()


async def _read_payload(request: Request) -> dict:
    ctype = request.headers.get("content-type", "")
    if "application/json" in ctype:
        return await request.json()
    form = await request.form()
    return {k: form[k] for k in form}


@router.post("/webhook/paypalych/success")
async def paypalych_success(request: Request) -> dict:
    payload = await _read_payload(request)

    inv_id = str(payload.get("InvId") or payload.get("order_id") or "")
    out_sum = str(payload.get("OutSum") or payload.get("amount") or "")
    signature = str(payload.get("SignatureValue") or payload.get("signature") or "")

    if not inv_id:
        raise HTTPException(status_code=400, detail="missing InvId")

    if not verify_postback_signature(out_sum, inv_id, signature):
        logger.warning("paypalych: bad signature for InvId={}", inv_id)
        raise HTTPException(status_code=403, detail="bad signature")

    try:
        order_id = int(inv_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="bad order_id")

    sessionmaker = request.app.state.sessionmaker
    bot = request.app.state.bot

    async with sessionmaker() as session:
        result = await process_payment(session, order_id)
        await session.commit()

    if result is not None:
        telegram_id, new_expire = result
        async with sessionmaker() as session:
            user = await UsersRepo(session).get_by_telegram_id(telegram_id)
        if user and user.subscription_url:
            await send_subscription_link(
                bot, telegram_id, user.subscription_url, new_expire.strftime("%d.%m.%Y")
            )

    logger.info("paypalych success processed order_id={}", order_id)
    return {"status": "ok"}


@router.post("/webhook/paypalych/fail")
async def paypalych_fail(request: Request) -> dict:
    payload = await _read_payload(request)
    inv_id = str(payload.get("InvId") or payload.get("order_id") or "")
    if not inv_id:
        return {"status": "ok"}

    try:
        order_id = int(inv_id)
    except ValueError:
        return {"status": "ok"}

    sessionmaker = request.app.state.sessionmaker
    async with sessionmaker() as session:
        from sqlalchemy import update

        from src.db.models import Order

        await session.execute(
            update(Order)
            .where(Order.id == order_id, Order.status == "pending")
            .values(status="failed")
        )
        await session.commit()

    logger.info("paypalych fail order_id={}", order_id)
    return {"status": "ok"}
