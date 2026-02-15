from datetime import datetime
from pydantic import BaseModel


class PostCreate(BaseModel):
    text: str


class PostResponse(BaseModel):
    id: int
    user_id: int
    body: str
    timestamp: datetime | None

    class Config:
        from_attributes = True
