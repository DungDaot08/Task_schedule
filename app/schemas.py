from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class MessageCreate(BaseModel):
    sender_id: int
    content: str


class MessageOut(BaseModel):
    id: int
    sender_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_time: Optional[datetime]
    remind_time: Optional[datetime]
