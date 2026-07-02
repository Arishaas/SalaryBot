import pytest
from app.services.product_service import create_product


@pytest.mark.asyncio
async def test_create_product(db, monkeypatch):

    async def fake_get_price_info(marketplace, product_id, url):
        return (1000, "Test Product")

    monkeypatch.setattr(
        "app.services.product_service.get_price_info",
        fake_get_price_info
    )

    product = await create_product(
        db=db,
        user_id=1,
        raw_input="https://www.wildberries.ru/catalog/123456/detail.aspx"
    )

    assert product.id is not None
    assert product.title == "Test Product"
    assert product.marketplace == "wb"


@pytest.mark.asyncio
async def test_duplicate_product(db, monkeypatch):

    async def fake_get_price_info(marketplace, product_id, url):
        return (1000, "Test Product")

    monkeypatch.setattr(
        "app.services.product_service.get_price_info",
        fake_get_price_info
    )

    url = "https://www.wildberries.ru/catalog/123456/detail.aspx"

    product1 = await create_product(db, 1, url)
    product2 = await create_product(db, 1, url)

    assert product1.id == product2.id