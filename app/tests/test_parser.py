from app.services.parser import parse_product_input


def test_parse_wildberries():
    url = "https://www.wildberries.ru/catalog/123456/detail.aspx"
    result = parse_product_input(url)

    assert result.marketplace == "wb"
    assert result.product_id == "123456"


def test_parse_ozon():
    url = "https://www.ozon.ru/product/test-987654/"
    result = parse_product_input(url)

    assert result.marketplace == "ozon"
    assert result.product_id == "987654"
