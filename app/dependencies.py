
from fastapi import Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, WebSession
from app.security import COOKIE_NAME, now


def get_web_session(request: Request, db: Session = Depends(get_db)):
    # 如果开辟了cookie，那么请求中会有Cookie: session_id=abc123xyz，这样sid就是abc123xyz
    sid = request.cookies.get(COOKIE_NAME)
    session = db.get(WebSession, sid) if sid else None
    return session if session and session.expires_at > now() else None

# 登录认证依赖函数，它的作用是：检查用户是否已经登录，并且确认数据库中仍然存在该用户。


def require_session(session: WebSession = Depends(get_web_session), db: Session = Depends(get_db)):
    if not session or not session.user_id or not db.get(User, session.user_id):
        # HTTP 401 表示 Unauthorized（未通过身份认证）。403	已识别用户，但没有访问权限
        raise HTTPException(401, "ログインしてください")
    return session


def require_api_user(session=Depends(get_web_session), db: Session = Depends(get_db)):
    if not session or not session.user_id or not db.get(User, session.user_id):
        raise HTTPException(401, "ログインしてください")
    return session
