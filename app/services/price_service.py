from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.services.parser import get_price


def update_prices(db: Session):
    products = db.query(Product).all()

    for product in products:
        new_price = get_price(product.url)

        last_price = (
            db.query(PriceHistory)
            .filter(PriceHistory.product_id == product.id)
            .order_by(desc(PriceHistory.created_at))
            .first()
        )

        if not last_price:
            db.add(PriceHistory(
                product_id=product.id,
                price=new_price
            ))
            continue

        if last_price != new_price:
            if new_price < last_price.price:
                print(f"Цена упала: {last_price.price} -> {new_price}")

            elif new_price > last_price.price:
                print(f"Цена выросла: {last_price.price} -> {new_price}")

            db.add(PriceHistory(
                product_id=product.id,
                price=new_price
            ))

    db.commit()
