from typing import Generator, Optional

from pydantic import BaseModel

from app.db.session import SessionLocal
from app import crud


class TokenData(BaseModel):
    username: Optional[str] = None


def get_db() -> Generator:
    db = SessionLocal()
    db.current_user_id = None
    try:
        yield db
    finally:
        db.close()
