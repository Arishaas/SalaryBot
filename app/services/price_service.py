from dataclasses import dataclass

from aiogram import Bot
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.price_history import PriceHistory
from app.models.product import Product
from app.models.user import User
from app.services.parser import get_price_info, marketplace_label

settings = get_settings()


@dataclass
class PriceChange:
    product: Product
    old_price: float
    new_price: float
    change_percent: float


def _calc_change_percent(old_price: float, new_price: float) -> float:
    if old_price == 0:
        return 0.0
    return ((new_price - old_price) / old_price) * 100


def _format_price(price: float) -> str:
    return f"{price:,.2f}".replace(",", " ").replace(".", ",") + " ₽"


def format_alert_message(change: PriceChange) -> str:
    product = change.product
    if change.new_price > change.old_price:
        header = "📈 Цена выросла!"
        direction = "выросла"
        mood = "🔺"
    else:
        header = "📉 Цена упала!"
        direction = "упала"
        mood = "🔻"
    sign = "+" if change.change_percent > 0 else ""
    title = product.title or f"Артикул {product.product_id}"

    return (
        f"⚡ <b>{header}</b>\n\n"
        f"📦 {title}\n"
        f"🏪 {marketplace_label(product.marketplace)}\n"
        f"💰 {_format_price(change.old_price)} → {_format_price(change.new_price)}\n"
        f"{mood} Цена {direction} на <b>{sign}{change.change_percent:.1f}%</b>\n"
        f"🔗 {product.url}"
    )


def format_weekly_report(changes: list[PriceChange]) -> str:
    if not changes:
        return (
            "📊 <b>Еженедельный отчёт</b>\n\n"
            "🎉 За неделю цены не изменились — всё стабильно!"
        )

    increases = [c for c in changes if c.change_percent > 0]
    decreases = [c for c in changes if c.change_percent < 0]
    unchanged = [c for c in changes if c.change_percent == 0]

    avg_change = sum(c.change_percent for c in changes) / len(changes)
    avg_sign = "+" if avg_change > 0 else ""

    if avg_change < 0:
        summary_mood = "🎉 В среднем подешевело!"
    elif avg_change > 0:
        summary_mood = "💸 В среднем подорожало"
    else:
        summary_mood = "😌 Цены стабильны"

    lines = [
        "📊 <b>Еженедельный отчёт</b>",
        "",
        summary_mood,
        f"📈 Среднее изменение: <b>{avg_sign}{avg_change:.1f}%</b>",
        f"🔺 Подорожало: {len(increases)}",
        f"🔻 Подешевело: {len(decreases)}",
        f"➖ Без изменений: {len(unchanged)}",
        "",
        "📝 <b>Детали:</b>",
    ]

    for change in changes:
        product = change.product
        if change.change_percent > 0:
            icon = "🔺"
        elif change.change_percent < 0:
            icon = "🔻"
        else:
            icon = "➖"
        sign = "+" if change.change_percent > 0 else ""
        title = product.title or f"Артикул {product.product_id}"
        lines.append(
            f"{icon} {title} ({marketplace_label(product.marketplace)}): "
            f"<b>{sign}{change.change_percent:.1f}%</b> "
            f"({_format_price(change.old_price)} → {_format_price(change.new_price)})"
        )

    return "\n".join(lines)


async def update_prices(db: Session, bot: Bot | None = None) -> list[PriceChange]:
    products = db.query(Product).all()
    alerts: list[PriceChange] = []

    for product in products:
        try:
            new_price, title = await get_price_info(
                product.marketplace, product.product_id, product.url
            )
        except Exception:
            continue

        if title and not product.title:
            product.title = title

        last_record = (
            db.query(PriceHistory)
            .filter(PriceHistory.product_id == product.id)
            .order_by(PriceHistory.created_at.desc())
            .first()
        )

        if not last_record:
            db.add(PriceHistory(product_id=product.id, price=new_price))
            continue

        old_price = last_record.price
        if old_price == new_price:
            continue

        change_percent = _calc_change_percent(old_price, new_price)
        db.add(PriceHistory(product_id=product.id, price=new_price))

        if abs(change_percent) >= settings.price_alert_threshold_percent:
            change = PriceChange(
                product=product,
                old_price=old_price,
                new_price=new_price,
                change_percent=change_percent,
            )
            alerts.append(change)

            if bot:
                user = db.query(User).filter(User.id == product.user_id).first()
                if user:
                    await bot.send_message(
                        user.chat_id,
                        format_alert_message(change),
                    )

    db.commit()
    return alerts


def get_weekly_changes(db: Session, user_id: int) -> list[PriceChange]:
    from datetime import datetime, timedelta

    week_ago = datetime.utcnow() - timedelta(days=7)
    products = db.query(Product).filter(Product.user_id == user_id).all()
    changes: list[PriceChange] = []

    for product in products:
        history = (
            db.query(PriceHistory)
            .filter(PriceHistory.product_id == product.id)
            .order_by(PriceHistory.created_at.asc())
            .all()
        )
        if not history:
            continue

        old_record = history[0]
        for record in history:
            if record.created_at >= week_ago:
                old_record = record
                break

        new_record = history[-1]
        old_price = old_record.price
        new_price = new_record.price
        change_percent = _calc_change_percent(old_price, new_price)

        changes.append(
            PriceChange(
                product=product,
                old_price=old_price,
                new_price=new_price,
                change_percent=change_percent,
            )
        )

    return changes


async def send_weekly_reports(db: Session, bot: Bot) -> None:
    users = db.query(User).all()
    for user in users:
        changes = get_weekly_changes(db, user.id)
        if not changes:
            continue
        report = format_weekly_report(changes)
        await bot.send_message(user.chat_id, report)
