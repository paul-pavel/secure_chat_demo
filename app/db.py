from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path


class UsersBase(DeclarativeBase):
    pass


class ChatBase(DeclarativeBase):
    pass


BASE_DIR = Path(__file__).resolve().parent.parent
USERS_DB_PATH = BASE_DIR / "users.sqlite3"
CHAT_DB_PATH = BASE_DIR / "chat.sqlite3"

users_engine = create_engine(f"sqlite:///{USERS_DB_PATH}", connect_args={"check_same_thread": False})
chat_engine = create_engine(f"sqlite:///{CHAT_DB_PATH}", connect_args={"check_same_thread": False})

UsersSessionLocal = sessionmaker(bind=users_engine, autoflush=False, autocommit=False)
ChatSessionLocal = sessionmaker(bind=chat_engine, autoflush=False, autocommit=False)


def init_db():
    from . import models  # noqa: F401 ensure models imported
    # Create tables in respective DBs
    UsersBase.metadata.create_all(bind=users_engine)
    ChatBase.metadata.create_all(bind=chat_engine)


def get_users_db():
    db = UsersSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_chat_db():
    db = ChatSessionLocal()
    try:
        yield db
    finally:
        db.close()
