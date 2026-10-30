from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, Date, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    realname: Mapped[str] = mapped_column(String(50))
    password: Mapped[str] = mapped_column(String(255))
    gender: Mapped[bool] = mapped_column(Boolean, default=True)


class Employee(Base):
    __tablename__ = "employee"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    salary: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    birthday: Mapped[date] = mapped_column(Date)
    photo: Mapped[str] = mapped_column(String(100), default="")


class WebSession(Base):
    """浏览器仅存随机标识；用户、验证码与 CSRF 令牌保存在数据库。"""
    __tablename__ = "web_session"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(nullable=True)
    csrf_token: Mapped[str] = mapped_column(String(64))
    captcha: Mapped[str | None] = mapped_column(String(10), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
