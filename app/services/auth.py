

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import RegisterInput
from app.security import hash_password, verify_password


def register(db: Session, data: RegisterInput):
    if db.scalar(select(User).where(User.username == data.username)):
        raise ValueError("このユーザー名は既に存在しています。")
    user = User(
        **data.model_dump(exclude={"password"}), password=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("このユーザー名は既に存在しています。") from None
    return user


def login(db: Session, username: str, password: str):
    user = db.scalar(select(User).where(User.username == username.strip()))
    if not user or not verify_password(password, user.password):
        raise ValueError("ユーザー名またはパスワードが間違っています。")
    return user
