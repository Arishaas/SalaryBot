from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.product import CreationProducts, OutProducts
from app.services.product_service import create_product, get_all_products
from app.services.price_service import update_prices
from app.services.user_service import get_or_create_user

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=OutProducts)
async def add_product(data: CreationProducts, db: Session = Depends(get_db)):
    if data.telegram_id is None:
        raise HTTPException(status_code=400, detail="telegram_id обязателен для API")
    user = get_or_create_user(db, data.telegram_id, data.telegram_id)
    return await create_product(db, user.id, data.url)


@router.get("/", response_model=list[OutProducts])
def product_list(db: Session = Depends(get_db)):
    return get_all_products(db)


@router.post("/update_prices")
async def update(db: Session = Depends(get_db)):
    await update_prices(db)
    return {"status": "ok"}
