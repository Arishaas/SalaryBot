from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    chat_id: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
