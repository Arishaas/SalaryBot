from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.product import CreationProducts, OutProducts
from app.services.product_service import create_product, get_all_products
from app.services.price_service import update_prices

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=OutProducts)
def add_product(data: CreationProducts, db: Session = Depends(get_db)):
    return create_product(db, data.url)


@router.get("/", response_model=list[OutProducts])
def product_list(db: Session = Depends(get_db)):
    return get_all_products(db)


@router.post("/update_prices")
def update(db: Session = Depends(get_db)):
    update_prices(db)
    return {"status": "ok"}
