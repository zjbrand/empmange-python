

from typing import Any

from fastapi import Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import BASE_DIR
from app.models import User, WebSession


templates = Jinja2Templates(directory=str(BASE_DIR/"app/templates"))


def render(
    request: Request,
    name: str,
    db: Session,
    session: WebSession | None = None,
    status_code: int = 200,
    **context: Any
) -> Response:
    user = db.get(
        User, session.user_id) if session and session.user_id else None
    return templates.TemplateResponse(request=request, name=name, context={
        "current_user": user, "csrf_token": session.csrf_token if session else "", **context
    }, status_code=status_code)
