from pydantic import BaseModel


class CreationProducts(BaseModel):
    url: str
    telegram_id: int | None = None


class OutProducts(BaseModel):
    id: int
    marketplace: str
    product_id: str
    url: str
    title: str | None = None

    class Config:
        from_attributes = True
