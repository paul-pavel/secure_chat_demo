from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.hash import bcrypt_sha256, bcrypt
from .db import get_users_db
from .models import User

import secrets
from typing import Optional


router = APIRouter()


SESSION_COOKIE = "scd_session"
_SESSION_STORE: dict[str, int] = {}
_SESSION_SECRET = secrets.token_urlsafe(32)


def get_db():
    yield from get_users_db()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    sid = request.cookies.get(SESSION_COOKIE)
    if not sid:
        return None
    user_id = _SESSION_STORE.get(sid)
    if not user_id:
        return None
    return db.get(User, user_id)


@router.get("/login")
def login_page(request: Request, user: Optional[User] = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/", status_code=302)
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory=str((request.app.state.templates_dir)))
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    ok = False
    if user:
        try:
            ok = bcrypt_sha256.verify(password, user.password_hash)
        except Exception:
            ok = False
        if not ok:
            try:
                ok = bcrypt.verify(password, user.password_hash)
            except Exception:
                ok = False
    if not user or not ok:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    sid = secrets.token_urlsafe(24)
    _SESSION_STORE[sid] = user.id
    resp = RedirectResponse(url="/", status_code=302)
    resp.set_cookie(SESSION_COOKIE, sid, httponly=True, samesite="lax")
    return resp


@router.get("/register")
def register_page(request: Request, user: Optional[User] = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/", status_code=302)
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory=str((request.app.state.templates_dir)))
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    username = username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username too short")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="User exists")
    # Use bcrypt_sha256 to support long passwords securely (pre-hash then bcrypt)
    user = User(username=username, password_hash=bcrypt_sha256.hash(password))
    db.add(user)
    db.commit()
    return RedirectResponse(url="/login", status_code=302)


@router.post("/logout")
def logout(request: Request, response: Response):
    sid = request.cookies.get(SESSION_COOKIE)
    if sid and sid in _SESSION_STORE:
        _SESSION_STORE.pop(sid, None)
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie(SESSION_COOKIE)
    return resp
