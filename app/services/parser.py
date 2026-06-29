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
    match = re.search(r"ozon\.(?:ru|com)/[^?\s]*/?(?:product/)?[^/\s]*-(\d+)", text, re.I)
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
    match = re.search(r"wb\.ru/catalog/(\d+)", text, re.I)
    if match:
        return match.group(1)
    return None


def _extract_yandex_id(text: str) -> str | None:
    match = re.search(
        r"market\.yandex\.(?:ru|by|kz|uz)/(?:product(?:--[^/?\s]+)?|card/[^/?\s]+)/(\d+)",
        text,
        re.I,
    )
    if match:
        return match.group(1)
    match = re.search(r"market\.yandex\.(?:ru|by|kz|uz)/product/(\d+)", text, re.I)
    if match:
        return match.group(1)
    return None


def _extract_aliexpress_id(text: str) -> str | None:
    match = re.search(r"aliexpress\.(?:ru|com)/item/(\d+)\.html", text, re.I)
    if match:
        return match.group(1)
    return None


def _build_product(marketplace: str, product_id: str) -> ParsedProduct:
    urls = {
        "ozon": f"https://www.ozon.ru/product/-{product_id}/",
        "wb": f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
        "yandex": f"https://market.yandex.ru/product--/{product_id}",
        "aliexpress": f"https://aliexpress.ru/item/{product_id}.html",
    }
    return ParsedProduct(marketplace=marketplace, product_id=product_id, url=urls[marketplace])


def parse_product_input(text: str) -> ParsedProduct:
    text = text.strip()

    extractors = [
        ("ozon", _extract_ozon_id),
        ("wb", _extract_wb_id),
        ("yandex", _extract_yandex_id),
        ("aliexpress", _extract_aliexpress_id),
    ]
    for marketplace, extractor in extractors:
        product_id = extractor(text)
        if product_id:
            return _build_product(marketplace, product_id)

    prefix_patterns = [
        (r"^(?:ozon|oz)[:\s-]+(\d+)$", "ozon"),
        (r"^(?:wb|wildberries)[:\s-]+(\d+)$", "wb"),
        (r"^(?:yandex|ym|яндекс)[:\s-]+(\d+)$", "yandex"),
        (r"^(?:aliexpress|ali|ae|али)[:\s-]+(\d+)$", "aliexpress"),
    ]
    for pattern, marketplace in prefix_patterns:
        match = re.match(pattern, text, re.I)
        if match:
            return _build_product(marketplace, match.group(1))

    if text.isdigit():
        raise ValueError(
            "🤔 Укажи маркетплейс: ozon:123, wb:123, yandex:123 или aliexpress:123, "
            "либо отправь полную ссылку."
        )

    raise ValueError(
        "⚠️ Поддерживаются только Ozon, Wildberries, Яндекс Маркет и AliExpress. "
        "Отправь ссылку или артикул."
    )


def parse_products(url: str) -> tuple[str, str]:
    parsed = parse_product_input(url)
    return parsed.marketplace, parsed.product_id


async def _fetch_page(url: str) -> str:
    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def _extract_title(html: str) -> str | None:
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    if title_match:
        return title_match.group(1).strip()
    json_title = re.search(r'"title"\s*:\s*"([^"]+)"', html)
    return json_title.group(1).strip() if json_title else None


async def _fetch_wb_price(product_id: str) -> tuple[float, str | None]:
    params = {
        "appType": 1,
        "curr": "rub",
        "dest": -1257786,
        "spp": 30,
        "nm": product_id,
    }
    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
        response = await client.get(WB_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

    products = data.get("data", {}).get("products", [])
    if not products:
        raise ValueError(f"Товар WB {product_id} не найден")

    product = products[0]
    price_kopecks = product.get("salePriceU") or product.get("priceU")
    if not price_kopecks:
        raise ValueError(f"Не удалось получить цену WB {product_id}")

    return price_kopecks / 100, product.get("name")


async def _fetch_ozon_price(url: str) -> tuple[float, str | None]:
    html = await _fetch_page(url)

    price_match = re.search(
        r'"price"\s*:\s*"?(\d+(?:\.\d+)?)"?|"finalPrice"\s*:\s*"?(\d+(?:\.\d+)?)"?',
        html,
    )
    if not price_match:
        price_match = re.search(r'data-price="(\d+(?:\.\d+)?)"', html)
    if not price_match:
        raise ValueError("Не удалось получить цену с Ozon")

    price_str = price_match.group(1) or price_match.group(2)
    return float(price_str), _extract_title(html)


async def _fetch_yandex_price(url: str) -> tuple[float, str | None]:
    html = await _fetch_page(url)

    price_match = re.search(
        r'"price"\s*:\s*\{[^}]*"value"\s*:\s*(\d+(?:\.\d+)?)',
        html,
    )
    if not price_match:
        price_match = re.search(r'"price"\s*:\s*(\d+(?:\.\d+)?)', html)
    if not price_match:
        price_match = re.search(r'data-auto="price-value"[^>]*>([^<]+)<', html)
    if not price_match:
        raise ValueError("Не удалось получить цену с Яндекс Маркета")

    price_str = re.sub(r"[^\d.]", "", price_match.group(1).replace(",", ".").replace("\xa0", ""))
    return float(price_str), _extract_title(html)


async def _fetch_aliexpress_price(url: str) -> tuple[float, str | None]:
    html = await _fetch_page(url)

    price_match = re.search(
        r'"minAmount"\s*:\s*\{[^}]*"value"\s*:\s*(\d+(?:\.\d+)?)',
        html,
    )
    if not price_match:
        price_match = re.search(
            r'"formattedPrice"\s*:\s*"[^"\d]*([\d\s\xa0,.]+)"',
            html,
        )
    if not price_match:
        price_match = re.search(r'"price"\s*:\s*"([\d\s,.]+)"', html)
    if not price_match:
        raise ValueError("Не удалось получить цену с AliExpress")

    price_str = re.sub(r"[^\d.]", "", price_match.group(1).replace(",", ".").replace("\xa0", ""))
    return float(price_str), _extract_title(html)


async def get_price_info(marketplace: str, product_id: str, url: str) -> tuple[float, str | None]:
    fetchers = {
        "wb": lambda: _fetch_wb_price(product_id),
        "ozon": lambda: _fetch_ozon_price(url),
        "yandex": lambda: _fetch_yandex_price(url),
        "aliexpress": lambda: _fetch_aliexpress_price(url),
    }
    fetcher = fetchers.get(marketplace)
    if not fetcher:
        raise ValueError(f"Неподдерживаемый маркетплейс: {marketplace}")
    return await fetcher()


async def get_price(url: str) -> float:
    marketplace, product_id = parse_products(url)
    price, _ = await get_price_info(marketplace, product_id, url)
    return price
