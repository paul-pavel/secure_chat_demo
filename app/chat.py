from fastapi import APIRouter, Depends, HTTPException, Request, Form, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, RedirectResponse
from .db import get_users_db, get_chat_db
from .models import User, Group, Message, Membership
from .auth import get_current_user
from datetime import datetime
from typing import Optional, Dict, Set, List
import json


router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.group_connections: Dict[int, Set[WebSocket]] = {}
        self.active_users: Dict[int, datetime] = {}
        self.active_connections: List[WebSocket] = []
        # map each websocket to the associated user id for per-group active lists
        self.ws_user: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, group_id: Optional[int] = None, user_id: Optional[int] = None):
        await websocket.accept()
        if group_id is not None:
            self.group_connections.setdefault(group_id, set()).add(websocket)
            if user_id is not None:
                self.active_users[user_id] = datetime.utcnow()
                self.ws_user[websocket] = user_id
        else:
            self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket, group_id: Optional[int] = None, user_id: Optional[int] = None):
        if group_id in self.group_connections:
            self.group_connections[group_id].discard(websocket)
        if user_id is not None:
            self.active_users.pop(user_id, None)
        # remove websocket mapping
        self.ws_user.pop(websocket, None)
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str, group_id: Optional[int] = None):
        if group_id is not None:
            conns = list(self.group_connections.get(group_id, set()))
            for ws in conns:
                try:
                    await ws.send_text(message)
                except RuntimeError:
                    # silently drop broken connections
                    self.group_connections[group_id].discard(ws)
                    self.ws_user.pop(ws, None)
        else:
            for connection in self.active_connections:
                await connection.send_text(message)


manager = ConnectionManager()


@router.get("/")
def index(request: Request, user: Optional[User] = Depends(get_current_user)):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory=str((request.app.state.templates_dir)))
    if not user:
        return HTMLResponse("<script>location='/login'</script>")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@router.get("/api/users/active")
def active_users(db: Session = Depends(get_users_db)):
    ids = list(manager.active_users.keys())
    users = db.query(User).filter(User.id.in_(ids)).all() if ids else []
    return [{"id": u.id, "username": u.username} for u in users]


@router.get("/api/groups/{group_id}/active_users")
def active_users_in_group(group_id: int, db: Session = Depends(get_users_db)):
    conns = manager.group_connections.get(group_id, set())
    user_ids: Set[int] = set()
    for ws in conns:
        uid = manager.ws_user.get(ws)
        if uid:
            user_ids.add(uid)
    users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
    return [{"id": u.id, "username": u.username} for u in users]


@router.get("/api/groups")
def list_groups(db: Session = Depends(get_chat_db)):
    groups = db.query(Group).all()
    return [{"id": g.id, "name": g.name} for g in groups]


@router.post("/api/groups")
def create_group(name: str, user: User = Depends(get_current_user), db: Session = Depends(get_chat_db)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Empty name")
    if db.query(Group).filter(Group.name == name).first():
        raise HTTPException(status_code=400, detail="Group exists")
    g = Group(name=name)
    db.add(g)
    db.flush()
    m = Membership(user_id=user.id, group_id=g.id)
    db.add(m)
    db.commit()
    return {"id": g.id, "name": g.name}


@router.post("/api/groups/join")
def join_group(group_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_chat_db)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    g = db.get(Group, group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Not found")
    if not db.query(Membership).filter_by(user_id=user.id, group_id=g.id).first():
        db.add(Membership(user_id=user.id, group_id=g.id))
        db.commit()
    return {"ok": True}


@router.get("/api/messages")
def get_messages(
    group_id: int,
    db_chat: Session = Depends(get_chat_db),
    db_users: Session = Depends(get_users_db),
):
    msgs = (
        db_chat.query(Message)
        .filter(Message.group_id == group_id)
        .order_by(Message.created_at.asc())
        .limit(100)
        .all()
    )
    author_ids = {m.author_id for m in msgs}
    users = db_users.query(User).filter(User.id.in_(author_ids)).all() if author_ids else []
    name_by_id = {u.id: u.username for u in users}
    return [
        {
            "id": m.id,
            "group_id": m.group_id,
            "author": name_by_id.get(m.author_id, f"user#{m.author_id}"),
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in msgs
    ]


@router.websocket("/ws/chat/{group_id}")
async def websocket_chat(
    websocket: WebSocket,
    group_id: int,
    db_chat: Session = Depends(get_chat_db),
    db_users: Session = Depends(get_users_db),
):
    # Simple auth via cookie-backed session
    from .auth import SESSION_COOKIE, _SESSION_STORE
    sid = websocket.cookies.get(SESSION_COOKIE)
    if not isinstance(sid, str):
        await websocket.close(code=4401)
        return
    user_id = _SESSION_STORE.get(sid)
    if not user_id:
        await websocket.close(code=4401)
        return
    user = db_users.get(User, user_id)
    if not user:
        await websocket.close(code=4401)
        return
    await manager.connect(websocket, group_id, user_id)
    try:
        await manager.broadcast(f"[system] {user.username} joined", group_id=group_id)
        while True:
            text = await websocket.receive_text()
            text = text.strip()
            if not text:
                continue
            
            created_at = datetime.utcnow()
            msg = Message(group_id=group_id, author_id=user_id, content=text)
            db_chat.add(msg)
            db_chat.commit()
            await manager.broadcast(json.dumps({
                "author": user.username,
                "content": text,
                "created_at": msg.created_at.isoformat()
            }), group_id=group_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, group_id, user_id)
        await manager.broadcast(f"[system] {user.username} left", group_id=group_id)


@router.websocket("/ws")
async def websocket_notifications(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # We can handle incoming messages here if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.post("/create_group")
async def create_group_form(
    name: str = Form(...),
    user: User = Depends(get_current_user),
    db_chat: Session = Depends(get_chat_db),
):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Empty name")
    if db_chat.query(Group).filter(Group.name == name).first():
        raise HTTPException(status_code=400, detail="Group exists")
    new_group = Group(name=name)
    db_chat.add(new_group)
    db_chat.commit()
    db_chat.refresh(new_group)

    # Add the creator to the group
    db_chat.add(Membership(user_id=user.id, group_id=new_group.id))
    db_chat.commit()

    await manager.broadcast(f"new_group:{new_group.name}")

    return RedirectResponse(url=f"/chat/{new_group.id}", status_code=303)


@router.get("/chat/{group_id}")
def chat_room(request: Request, group_id: int, user: User = Depends(get_current_user)):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory=str((request.app.state.templates_dir)))
    return templates.TemplateResponse("chat.html", {"request": request, "user": user, "group_id": group_id})
