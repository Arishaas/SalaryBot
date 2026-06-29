from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

BTN_LIST = "📋 Список"
BTN_ADD = "➕ Добавить"
BTN_HELP = "❓ Справка"

MENU_BUTTONS = {BTN_LIST, BTN_ADD, BTN_HELP}

MARKETPLACE_EMOJI = {
    "ozon": "🟠",
    "wb": "🟣",
    "yandex": "🟡",
    "aliexpress": "🔴",
}


def marketplace_emoji(marketplace: str) -> str:
    return MARKETPLACE_EMOJI.get(marketplace, "🏪")


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_LIST), KeyboardButton(text=BTN_ADD)],
            [KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
    )


def products_keyboard(product_ids: list[int]) -> InlineKeyboardMarkup | None:
    if not product_ids:
        return None
    rows = [
        [InlineKeyboardButton(text=f"🗑 Удалить #{pid}", callback_data=f"remove:{pid}")]
        for pid in product_ids
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
