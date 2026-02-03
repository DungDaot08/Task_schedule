from sqlalchemy import (
    Column, Integer, String, Text,
    ForeignKey, DateTime, UniqueConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    sender = relationship("User")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text)

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime)
    remind_time = Column(DateTime)

    source_message_id = Column(Integer, ForeignKey("messages.id"))
    created_at = Column(DateTime, server_default=func.now())

    assignees = relationship(
        "TaskAssignee",
        cascade="all, delete-orphan"
    )


class TaskAssignee(Base):
    __tablename__ = "task_assignees"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("task_id", "user_id", name="uq_task_user"),
    )
