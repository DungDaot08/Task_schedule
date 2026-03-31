from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from uuid import UUID


class MessageCreate(BaseModel):
    content: str


class MessageOut(BaseModel):
    id: UUID
    sender_id: UUID
    content: str
    created_at: datetime
    generated_task_id: Optional[UUID]

    class Config:
        from_attributes = True
        orm_mode = True


class TaskOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    start_time: Optional[datetime]
    remind_time: Optional[datetime]


class UserOut(BaseModel):
    id: UUID
    username: str
    # password: str

    class Config:
        orm_mode = True


class TaskAssigneeOut(BaseModel):
    user_id: UUID

    class Config:
        orm_mode = True


class TaskOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    creator_id: UUID
    start_time: Optional[datetime] = None
    remind_time: Optional[datetime] = None
    created_at: datetime
    assignees: list[TaskAssigneeOut]

    class Config:
        orm_mode = True
