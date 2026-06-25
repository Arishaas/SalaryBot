import re


def parse_products(url: str):
    if "ozon" in url:
        return "oz", "123"

    if "wildberries" in url:
        return "wb", "456"

    raise ValueError("Unexpected marketplace")


def get_price(url: str) -> float:
    return 80.00
