from sqlalchemy.orm import Session

from app.models.product import Product
from app.services.parser import get_price_info, parse_product_input


async def create_product(db: Session, user_id: int, raw_input: str) -> Product:
    parsed = parse_product_input(raw_input)

    marketplace = parsed.marketplace
    product_id = parsed.product_id
    url = parsed.url

    existing = (
        db.query(Product)
        .filter(
            Product.user_id == user_id,
            Product.marketplace == marketplace,
            Product.product_id == product_id,
        )
        .first()
    )
    if existing:
        return existing

    # ✔ получаем tuple (price, title)
    price, title = await get_price_info(marketplace, product_id, url)

    product = Product(
        user_id=user_id,
        marketplace=marketplace,
        product_id=product_id,
        url=url,
        title=title,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    # ✔ сохраняем цену в историю
    from app.models.price_history import PriceHistory

    db.add(
        PriceHistory(
            product_id=product.id,
            price=price
        )
    )
    db.commit()

    return product


def get_user_products(db: Session, user_id: int) -> list[Product]:
    return db.query(Product).filter(Product.user_id == user_id).all()


def get_all_products(db: Session) -> list[Product]:
    return db.query(Product).all()


def delete_product(db: Session, user_id: int, product_id: int) -> bool:
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.user_id == user_id)
        .first()
    )
    if not product:
        return False

    db.delete(product)
    db.commit()
    return True