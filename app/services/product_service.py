from sqlalchemy.orm import Session
from app.models.product import Product
from app.services.parser import parse_products


def create_product(db: Session, url: str):
    marketplace, product_id = parse_products(url)

    product = Product(
        marketplace=marketplace,
        product_id=product_id,
        url=url
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def get_all_products(db: Session):
    return db.query(Product).all()
