
from io import BytesIO
from uuid import uuid4

from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException, UploadFile
from sqlalchemy import select
import logging

from app.config import MAX_IMAGE_BYTES, UPLOAD_DIR
from app.models import Employee

logger = logging.getLogger(__name__)


def lists(db, *, name=None, salary_min=None, salary_max=None, date_begin=None, date_end=None):
    query = select(Employee)
    if name and name.strip():
        query = query.where(Employee.name.contains(
            name.strip(), autoescape=True))
    if salary_min is not None:
        query = query.where(Employee.salary >= salary_min)
    if salary_max is not None:
        query = query.where(Employee.salary <= salary_max)
    if date_begin is not None:
        query = query.where(Employee.birthday >= date_begin)
    if date_end is not None:
        query = query.where(Employee.birthday <= date_end)
    return list(db.scalars(query.order_by(Employee.id)))


def remove_photo(filename):
    if not filename:
        return
    path = (UPLOAD_DIR / filename).resolve()
    if path.parent == UPLOAD_DIR:
        try:
            # （ファイルパス）が指すファイルを削除します。
            # missing_ok=True: ファイルが存在しなかった場合の挙動を指定するオプションです。
            # True の場合：ファイルがすでに存在していなくても、エラー（FileNotFoundError）を発生させず、そのまま何事もなく処理を続行します。
            # False（デフォルト）の場合：ファイルが存在しないと FileNotFoundError が発生します。
            path.unlink(missing_ok=True)
        except OSError:
            logger.exception("写真削除失敗: %s", path.name)


def find(db, employee_id):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(404, "社員が見つかりません。")
    return employee


def store_photo(upload: UploadFile | None) -> str | None:
    if upload is None or not upload.filename:
        return None
    # 它是 FastAPI UploadFile 内部持有的类文件对象，通常由 SpooledTemporaryFile 实现文件对象与二进制读取，
    # 较小文件可以先保存在内存中，较大文件可能转存到临时磁盘文件。
    # 如果刚好读取 5,242,880 字节，文件可能符合要求。如果读取到 5,242,881 字节，就可以确定文件超过了上限。
    # 这样不需要把一个可能非常大的文件全部读取进内存。读取结果 content 的类型是 bytes。
    content = upload.file.read(MAX_IMAGE_BYTES + 1)
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError("画像は5MB以下にしてください。")
    try:
        # BytesIO 会把这些字节包装成一个内存中的类文件对象。就是让 Pillow 从内存中的字节读取图片，而不必先把它保存到硬盘。
        # with ... as image,这是 Python 的上下文管理语法。它能够在退出 with 代码块时清理 Pillow 使用的相关资源。
        with Image.open(BytesIO(content)) as image:
            # 根据图片文件内容识别图片格式,image.format 是 Pillow 解析文件得到的格式，比单纯查看扩展名更可靠
            image_format = image.format
            # 集合（set），不是字典。
            if image_format not in {"PNG", "JPEG", "GIF"}:
                raise ValueError("PNG、JPEG、GIF の画像を選択してください。")
            # Pillow 用于检查图像文件完整性和基本结构的方法。例如，如果文件内容损坏，Pillow 可能抛出异常。
            image.verify()
    # UnidentifiedImageError无法识别图片 OSError文件损坏或读取过程中发生问题 DecompressionBombError图片像素数量异常巨大，可能造成资源消耗问题
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        # from None がない場合:ユーザーには不要な、ライブラリ内部の複雑なエラー情報やスタックトレースが一緒に表示されてしまいます。
        # from None がある場合:余計な内部エラーを隠し、「正しい画像ファイルを選択してください。」というメッセージのみをきれいにユーザーへ伝えることができます。
        # 异常链控制
        raise ValueError("正しい画像ファイルを選択してください。") from None
    # .hex 将 UUID 表示成 32 个十六进制字符（不含连字符）。
    # {"PNG": ".png", "JPEG": ".jpg","GIF": ".gif"}[image_format]=字典[key]
    name = uuid4().hex + {"PNG": ".png", "JPEG": ".jpg",
                          "GIF": ".gif"}[image_format]
    # 相当于with open(UPLOAD_DIR / name, "wb") as f: f.write(content)，wb 表示以二进制写入模式打开文件
    (UPLOAD_DIR / name).write_bytes(content)
    return name


def save(db, data, upload=None, employee_id=None):
    # 新增和修改使用同一套逻辑，如果是新增employee = Employee(photo="")创建一个新的 SQLAlchemy ORM 对象
    employee = find(
        db, employee_id) if employee_id is not None else Employee(photo="")
    old_photo = employee.photo
    new_photo = store_photo(upload)
    # model_dump() 的作用是把 Pydantic 模型转换成 Python 字典。.items()返回字典中的键值对，供循环遍历。
    # 循环	key	      value
    # 1	  "name"	  "田中太郎"
    # 2   "salary"	   Decimal("350000")
    # 3	  "birthday"   date(1995, 1, 1)
    for key, value in data.model_dump().items():
        # setattr() 动态修改对象属性,setattr(对象, 属性名称, 属性值)
        setattr(employee, key, value)
    if new_photo:
        employee.photo = new_photo
    db.add(employee)
    try:
        db.commit()
    except Exception:
        db.rollback()
        remove_photo(new_photo)
        raise
    if new_photo:
        remove_photo(old_photo)
    logger.info("社員保存 id=%s", employee.id)
    return employee


def delete(db, employee_id):
    employee = find(db, employee_id)
    photo = employee.photo
    db.delete(employee)
    db.commit()
    remove_photo(photo)
    logger.info("社員削除 id=%s", employee_id)
