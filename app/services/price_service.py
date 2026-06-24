from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.services.parser import get_price


def update_prices(db: Session):
    products = db.query(Product).all()

    for product in products:
        price = get_price(product.url)

        price_record = PriceHistory(
            product_id=product.id,
            price=price
        )

        db.add(price_record)
    db.commit()
