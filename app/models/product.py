from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace: Mapped[str]
    product_id: Mapped[int]
    url: Mapped[str]
