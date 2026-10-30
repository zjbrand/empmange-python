

from io import BytesIO
import secrets

from PIL import Image, ImageDraw, ImageFont
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_web_session
from app.models import WebSession
from app.schemas import RegisterInput
from app.security import COOKIE_NAME, check_csrf, create_session, set_cookie
from app.services import auth
from app.views import render


router = APIRouter(tags=["認証"])


@router.get("/login")
@router.get("/register")
def page(request: Request, db=Depends(get_db), session=Depends(get_web_session)):
    session = session or create_session(db)
    response = render(request, "regist.html" if request.url.path ==
                      "/register" else "login.html", db, session)
    set_cookie(response, session)
    return response


@router.get("/user/generateImageCode")
def captcha(db=Depends(get_db), session=Depends(get_web_session)):
    session = session or create_session(db)
    # 这里的 _ 只是表示循环变量不需要使用
    code = "".join(secrets.choice("23456789ABCDEFGHJKLMNPQRSTUVWXYZ")
                   for _ in range(4))
    session.captcha = code
    db.commit()
    # Pillow（PIL）图像处理库动态生成验证码图片
    # 使用红、绿、蓝三色模式,宽 180 像素，高 50 像素,图片背景颜色:浅绿色"#edf4f0"
    image = Image.new("RGB", (180, 50), "#edf4f0")
    # 创建一个绘图对象,也可以加载系统字体：font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)
    draw = ImageDraw.Draw(image)
    # 加载 Pillow 默认字体，并指定字号为 32。
    font = ImageFont.load_default(size=32)
    for _ in range(8):
        # 干扰直线四个坐标，如 (15,10,150,35)用 (15,10）和（150,35)两个点画一条直线。
        draw.line(tuple(secrets.randbelow(180 if i % 2 == 0 else 50)
                  for i in range(4)), fill="#aabbb0")
    # (35, 6)：文字起始绘制坐标。
    draw.text((35, 6), code, font=font, fill="#234c3b")
    buffer = BytesIO()
    # image.save("captcha.png")这样会在硬盘中写入文件，而这里只要写在内存中交给前端就可以
    image.save(buffer, format="PNG")
    # buffer.getvalue() 获取内存中的全部图片字节
    # Cache-Control: no-store要求浏览器等缓存不要保存这次响应，有利于避免验证码图片被缓存
    response = Response(buffer.getvalue(), media_type="image/png",
                        headers={"Cache-Control": "no-store"})
    set_cookie(response, session)
    return response


@router.post("/user/register")
# Form()从 HTTP 表单中获取数据 ""没有提供该字段时使用空字符串
def register(request: Request, username: str = Form(""), realname: str = Form(""), password: str = Form(""),
             gender: str = Form("true"), code: str = Form(""), csrf_token: str = Form(""), db: Session = Depends(get_db),
             session: WebSession | None = Depends(get_web_session)):
    if not session:
        # 303告诉浏览器：当前 POST请求处理结束，请通过 GET方法访问另一个地址。可以避免浏览器跳转时继续重复提交 POST 请求
        return RedirectResponse("/register", status_code=303)
    check_csrf(session, csrf_token)
    expected = session.captcha
    session.captcha = None
    db.commit()
    try:
        if not expected or not secrets.compare_digest(expected, code.strip().upper()):
            raise ValueError("検証コードが間違っているか、又は有効期限が切れています。")
        data = RegisterInput(
            username=username, realname=realname, password=password, gender=gender)
        auth.register(db, data)
    except (ValueError, TypeError) as exc:
        message = "入力内容を確認してください（パスワードは6～128文字）。" if isinstance(
            exc, ValidationError) else str(exc)
        return render(request, "regist.html", db, session, status_code=400, error=message,
                      values={"username": username, "realname": realname, "gender": gender})
    return RedirectResponse("/login?registered=1", status_code=303)


@router.post("/user/login")
def login(requst: Request, username: str = Form(""), password: str = Form(""), csrf_token: str = Form(""),
          db=Depends(get_db), session=Depends(get_web_session)):
    if not session:
        return RedirectResponse("/login", status_code=303)
    check_csrf(session, csrf_token)
    try:
        if len(password) > 128:
            raise ValueError("ユーザー名またはパスワードが間違っています。")
        user = auth.login(db, username, password)
    except ValueError as exc:
        return render(requst, "login.html", db, session, status_code=400, error=str(exc), username=username)
    db.delete(session)
    db.commit()
    new_session = create_session(db, user.id)
    response = RedirectResponse("/employee/lists", status_code=303)
    set_cookie(response, new_session)
    return response


@router.post("/user/logout")
def logout(csrf_token: str = Form(""), db=Depends(get_db), session=Depends(get_web_session)):
    if session:
        check_csrf(session, csrf_token)
        db.delete(session)
        db.commit()
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(COOKIE_NAME, path="/")
    return response
