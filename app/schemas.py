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


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True


class MessageOut(BaseModel):
    id: int
    sender_id: int
    content: str
    created_at: datetime

    class Config:
        orm_mode = True


class TaskAssigneeOut(BaseModel):
    user_id: int

    class Config:
        orm_mode = True


class TaskOut(BaseModel):
    id: int
    title: str
    description: str | None
    creator_id: int
    start_time: datetime | None
    remind_time: datetime | None
    created_at: datetime
    assignees: list[TaskAssigneeOut]

    class Config:
        orm_mode = True
