
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterInput(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    realname: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    gender: bool = True

    # # field_validator 是一个装饰器（Decorator）。它告诉 Pydantic：在验证 username 和 realname 这两个字段时，先执行下面的 strip_text() 函数
    # before	在 Pydantic 内部类型转换和字段验证之前执行
    @field_validator("username", "realname", mode="before")
    @classmethod
    # cls 代表 RegisterInput 类,当前函数没有使用 cls。value 是当前需要验证的字段值。
    def strip_text(cls, value):
        # isinstance()：检查对象类型,是str返回true
        return value.strip() if isinstance(value, str) else value


class EmployeeInput(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    salary: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    birthday: date

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("birthday", mode="before")
    @classmethod
    def normalize_date(cls, value):
        return value.replace("/", "-") if isinstance(value, str) else value


class EmployeeRead(EmployeeInput):
    # from_attributes=True は、「Pythonのオブジェクト（辞書型だけでなく、
    # SQLAlchemyなどのORMモデルのインスタンスなど）の属性からデータを読み取れるようにする」という設定です。
    model_config = ConfigDict(from_attributes=True)
    id: int
    photo: str
