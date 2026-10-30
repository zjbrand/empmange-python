

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

from fastapi import HTTPException, Response
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import COOKIE_SECURE
from app.models import WebSession


COOKIE_NAME = "empmanage_session"


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_session(db: Session, user_id=None):
    db.execute(delete(WebSession).where(WebSession.expires_at < now()))
    # CSRF 是 Cross-Site Request Forgery，即跨站请求伪造攻击
    session = WebSession(id=secrets.token_urlsafe(32), user_id=user_id,
                         csrf_token=secrets.token_urlsafe(32), expires_at=now() + timedelta(hours=2))
    db.add(session)
    db.commit()
    return session


def set_cookie(response: Response, session: WebSession):
    # secure=False,浏览器在 HTTP 和 HTTPS 连接下都可以发送这个 Cookie。
    # samesite="lax"允许跨站的“常规导航”携带 Cookie,如果用户在别的网站（比如知乎或谷歌）点击了一个链接，
    # 跳转到你的网站（属于跨站 GET 请求），浏览器会携带这个 Cookie。
    # 禁止跨站的“子资源/API 请求”携带 Cookie：如果其他网站通过 <img> 标签、<iframe> 框架
    # 或者 fetch/AJAX 异步请求加载你网站的资源，浏览器不会携带这个 Cookie。
    # path="/" 表示根路径：代表这个 Cookie 对整个网站的所有页面和接口都有效。
    response.set_cookie(COOKIE_NAME, session.id, max_age=7200,
                        httponly=True, secure=COOKIE_SECURE, samesite="lax", path="/")


def check_csrf(session: WebSession, token: str):
    # hmac.compare_digest() 采用的是恒定时间比较（Constant-time comparison），无论在哪一个位置出错，耗费的时间都是恒定的，从而有效防止时序侧信道攻击
    if not token or not hmac.compare_digest(session.csrf_token, token):
        raise HTTPException(403, "フォームの有効期限が切れています。画面を再読み込みしてください。")


def hash_password(password: str) -> str:
    # 标准库 PBKDF2，独立随机盐；不沿用旧项目 MD5。
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 600_000).hex()
    return f"pbkdf2_sha256$600000${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, rounds, salt, digest = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        # "sha256"	使用 SHA-256 作为底层哈希算法
        # password.encode()	将密码字符串转换为字节
        # salt.encode()	将盐字符串转换为字节
        # 600_000	PBKDF2 迭代次数
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), int(rounds)).hex()
        return hmac.compare_digest(actual, digest)
    except (ValueError, TypeError):
        return False
