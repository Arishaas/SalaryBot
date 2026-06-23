from pydantic import BaseModel


class CreationProducts(BaseModel):
    url: str


class OutProducts(BaseModel):
    id: int
    marketplace: str
    product_id: int
    url: str

    class Config:
        from_attributes = True
