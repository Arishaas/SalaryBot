import re
from dataclasses import dataclass

import httpx

WB_API_URL = "https://card.wb.ru/cards/v2/detail"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
}

MARKETPLACE_LABELS = {
    "ozon": "Ozon",
    "wb": "Wildberries",
    "yandex": "Яндекс Маркет",
    "aliexpress": "AliExpress",
}


@dataclass
class ParsedProduct:
    marketplace: str
    product_id: str
    url: str


def marketplace_label(marketplace: str) -> str:
    return MARKETPLACE_LABELS.get(marketplace, marketplace)


def _extract_ozon_id(text: str) -> str | None:
    match = re.search(r"ozon\.(?:ru|com)/.*-(\d+)", text, re.I)
    if match:
        return match.group(1)
    match = re.search(r"ozon\.(?:ru|com)/product/(\d+)", text, re.I)
    if match:
        return match.group(1)
    return None


def _extract_wb_id(text: str) -> str | None:
    match = re.search(r"wildberries\.(?:ru|by|kz)/catalog/(\d+)", text, re.I)
    if match:
        return match.group(1)
    return None


def _extract_yandex_id(text: str) -> str | None:
    match = re.search(r"market\.yandex\.(?:ru|by|kz|uz)/.*?/(\d+)", text, re.I)
    return match.group(1) if match else None


def _extract_aliexpress_id(text: str) -> str | None:
    match = re.search(r"aliexpress\.(?:ru|com)/item/(\d+)", text, re.I)
    return match.group(1) if match else None


def _build_product(marketplace: str, product_id: str) -> ParsedProduct:
    urls = {
        "ozon": f"https://www.ozon.ru/product/-{product_id}/",
        "wb": f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
        "yandex": f"https://market.yandex.ru/product--/{product_id}",
        "aliexpress": f"https://aliexpress.ru/item/{product_id}.html",
    }
    return ParsedProduct(marketplace, product_id, urls[marketplace])


def parse_product_input(text: str) -> ParsedProduct:
    text = text.strip()

    # ссылки
    for name, extractor in [
        ("ozon", _extract_ozon_id),
        ("wb", _extract_wb_id),
        ("yandex", _extract_yandex_id),
        ("aliexpress", _extract_aliexpress_id),
    ]:
        product_id = extractor(text)
        if product_id:
            return _build_product(name, product_id)

    # формат ozon:123
    patterns = [
        (r"^(ozon|oz):(\d+)$", "ozon"),
        (r"^(wb):(\d+)$", "wb"),
        (r"^(yandex|ym):(\d+)$", "yandex"),
        (r"^(ali|ae):(\d+)$", "aliexpress"),
    ]

    for pattern, marketplace in patterns:
        match = re.match(pattern, text)
        if match:
            return _build_product(marketplace, match.group(2))

    raise ValueError("❌ Неверный формат. Отправь ссылку или ozon:123")


async def _fetch_page(url: str) -> str:
    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def _extract_title(html: str) -> str | None:
    match = re.search(r"<h1[^>]*>([^<]+)</h1>", html)
    return match.group(1).strip() if match else None


async def _fetch_wb_price(product_id: str):
    params = {
        "appType": 1,
        "curr": "rub",
        "nm": product_id,
    }

    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
        r = await client.get(WB_API_URL, params=params)
        r.raise_for_status()
        data = r.json()

    products = data.get("data", {}).get("products", [])
    if not products:
        raise ValueError("WB товар не найден")

    product = products[0]

    price = (
        product.get("salePriceU")
        or product.get("priceU")
        or product.get("clientPriceU")
    )

    if not price:
        raise ValueError("WB цена не найдена")

    return price / 100, product.get("name")


async def _fetch_ozon_price(url: str):
    html = await _fetch_page(url)

    match = re.search(
        r'"price"\s*:\s*"?(\d+(?:\.\d+)?)"?'
        r'|"finalPrice"\s*:\s*"?(\d+(?:\.\d+)?)"?'
        r'|"cardPrice"\s*:\s*"?(\d+(?:\.\d+)?)"?',
        html,
    )

    if not match:
        raise ValueError("Ozon цена не найдена")

    price = next(filter(None, match.groups()))
    return float(price), _extract_title(html)


async def _fetch_yandex_price(url: str):
    html = await _fetch_page(url)

    match = re.search(r'"value"\s*:\s*(\d+(?:\.\d+)?)', html)

    if not match:
        raise ValueError("Яндекс цена не найдена")

    return float(match.group(1)), _extract_title(html)


async def _fetch_aliexpress_price(url: str):
    html = await _fetch_page(url)

    match = re.search(r'"value"\s*:\s*(\d+(?:\.\d+)?)', html)

    if not match:
        raise ValueError("Ali цена не найдена")

    return float(match.group(1)), _extract_title(html)


async def get_price_info(marketplace: str, product_id: str, url: str):
    if marketplace == "wb":
        return await _fetch_wb_price(product_id)
    if marketplace == "ozon":
        return await _fetch_ozon_price(url)
    if marketplace == "yandex":
        return await _fetch_yandex_price(url)
    if marketplace == "aliexpress":
        return await _fetch_aliexpress_price(url)

    raise ValueError("Неизвестный маркетплейс")


async def get_price(text: str):
    parsed = parse_product_input(text)
    return await get_price_info(parsed.marketplace, parsed.product_id, parsed.url)
