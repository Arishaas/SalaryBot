from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import (
    BTN_ADD,
    BTN_HELP,
    BTN_LIST,
    MENU_BUTTONS,
    main_keyboard,
    marketplace_emoji,
    products_keyboard,
)
from app.database import SessionLocal
from app.services.parser import marketplace_label
from app.services.product_service import create_product, delete_product, get_user_products
from app.services.user_service import get_or_create_user

router = Router()

WELCOME_TEXT = (
    "🛒 <b>Бот отслеживания цен</b>\n\n"
    "Учебный проект, который следит за ценами на маркетплейсах — "
    "и реально работает! 😊\n\n"
    "🏪 <b>Маркетплейсы:</b> Ozon, Wildberries, Яндекс Маркет, AliExpress\n\n"
    "✨ <b>Как пользоваться:</b>\n"
    "• Нажми «➕ Добавить» и отправь ссылку или артикул\n"
    "• «📋 Список» — все отслеживаемые товары\n"
    "• Раз в неделю — отчёт 📊\n"
    "• Резкое изменение цены — сразу уведомление ⚡\n\n"
    "Погнали! 🚀"
)

ADD_PROMPT = (
    "➕ <b>Добавление товара</b>\n\n"
    "Отправь ссылку или артикул:\n"
    "🟠 <code>ozon:123456</code>\n"
    "🟣 <code>wb:123456</code>\n"
    "🟡 <code>yandex:123456</code>\n"
    "🔴 <code>aliexpress:123456</code>"
)


def _format_product_list(products) -> str:
    lines = ["📋 <b>Твои товары:</b>\n"]
    for product in products:
        emoji = marketplace_emoji(product.marketplace)
        title = product.title or f"Артикул {product.product_id}"
        lines.append(
            f"{emoji} <b>#{product.id}</b> — {title}\n"
            f"   {marketplace_label(product.marketplace)} · {product.url}"
        )
    lines.append("\n👇 Нажми кнопку, чтобы удалить товар")
    return "\n".join(lines)


async def _send_product_list(message: Message, user_id: int) -> None:
    db = SessionLocal()
    try:
        products = get_user_products(db, user_id)
        if not products:
            await message.answer(
                "📭 <b>Список пуст</b>\n\n"
                "Пока ничего не отслеживается.\n"
                "Нажми «➕ Добавить» и отправь ссылку на товар! 😉",
                reply_markup=main_keyboard(),
            )
            return

        await message.answer(
            _format_product_list(products),
            reply_markup=products_keyboard([p.id for p in products]),
        )
    finally:
        db.close()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    db = SessionLocal()
    try:
        get_or_create_user(db, message.from_user.id, message.chat.id)
    finally:
        db.close()
    await message.answer(WELCOME_TEXT, reply_markup=main_keyboard())


@router.message(Command("help"))
@router.message(F.text == BTN_HELP)
async def cmd_help(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=main_keyboard())


@router.message(Command("list"))
@router.message(F.text == BTN_LIST)
async def cmd_list(message: Message) -> None:
    db = SessionLocal()
    try:
        user = get_or_create_user(db, message.from_user.id, message.chat.id)
        await _send_product_list(message, user.id)
    finally:
        db.close()


@router.message(F.text == BTN_ADD)
async def cmd_add_prompt(message: Message) -> None:
    await message.answer(ADD_PROMPT, reply_markup=main_keyboard())


@router.callback_query(F.data.startswith("remove:"))
async def cb_remove_product(callback: CallbackQuery) -> None:
    product_id = int(callback.data.split(":", 1)[1])
    db = SessionLocal()
    try:
        user = get_or_create_user(db, callback.from_user.id, callback.message.chat.id)
        if delete_product(db, user.id, product_id):
            await callback.answer(f"🗑 Товар #{product_id} удалён!")
            products = get_user_products(db, user.id)
            if products:
                await callback.message.edit_text(
                    _format_product_list(products),
                    reply_markup=products_keyboard([p.id for p in products]),
                )
            else:
                await callback.message.edit_text(
                    "📭 <b>Список пуст</b>\n\nМожно добавить новый товар через «➕ Добавить» ✨"
                )
        else:
            await callback.answer("😕 Товар не найден", show_alert=True)
    finally:
        db.close()


@router.message(Command("remove"))
async def cmd_remove(message: Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer(
            "🗑 Открой «📋 Список» и нажми кнопку «Удалить» у нужного товара.",
            reply_markup=main_keyboard(),
        )
        return

    product_id = int(parts[1].strip())
    db = SessionLocal()
    try:
        user = get_or_create_user(db, message.from_user.id, message.chat.id)
        if delete_product(db, user.id, product_id):
            await message.answer(
                f"✅ Товар #{product_id} удалён из списка!",
                reply_markup=main_keyboard(),
            )
        else:
            await message.answer("😕 Товар не найден.", reply_markup=main_keyboard())
    finally:
        db.close()


@router.message(F.text)
async def handle_product_input(message: Message) -> None:
    if message.text.startswith("/") or message.text in MENU_BUTTONS:
        return

    db = SessionLocal()
    try:
        user = get_or_create_user(db, message.from_user.id, message.chat.id)
        try:
            product = await create_product(db, user.id, message.text.strip())
        except ValueError as exc:
            await message.answer(f"⚠️ {exc}", reply_markup=main_keyboard())
            return
        except Exception:
            await message.answer(
                "😔 Не удалось получить цену.\n"
                "Проверь ссылку или артикул и попробуй ещё раз!",
                reply_markup=main_keyboard(),
            )
            return

        emoji = marketplace_emoji(product.marketplace)
        title = product.title or f"Артикул {product.product_id}"
        await message.answer(
            f"✅ <b>Товар добавлен!</b>\n\n"
            f"📦 {title}\n"
            f"{emoji} {marketplace_label(product.marketplace)}\n"
            f"🔗 {product.url}\n\n"
            f"🔖 ID: <b>#{product.id}</b>\n"
            f"Буду следить за ценой 👀",
            reply_markup=main_keyboard(),
        )
    finally:
        db.close()
