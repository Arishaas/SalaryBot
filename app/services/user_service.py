from sqlalchemy.orm import Session

from app.models.user import User


def get_or_create_user(db: Session, telegram_id: int, chat_id: int) -> User:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        if user.chat_id != chat_id:
            user.chat_id = chat_id
            db.commit()
            db.refresh(user)
        return user

    user = User(telegram_id=telegram_id, chat_id=chat_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_telegram_id(db: Session, telegram_id: int) -> User | None:
    return db.query(User).filter(User.telegram_id == telegram_id).first()
