from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    UniqueConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy.dialects.postgresql import ARRAY
import uuid
from sqlalchemy.dialects.postgresql import UUID

# =========================
# USERS
# =========================


class User(Base):
    __tablename__ = "users"

    # id = Column(Integer, primary_key=True, index=True)
    id = Column(UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    messages = relationship("Message", back_populates="sender")
    created_tasks = relationship("Task", back_populates="creator")


# =========================
# MESSAGES
# =========================
class Message(Base):
    __tablename__ = "messages"

    # id = Column(Integer, primary_key=True, index=True)

    # sender_id = Column(
    #    Integer,
    #    ForeignKey("users.id"),
    #    nullable=False
    # )

    id = Column(UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, index=True)

    sender_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    content = Column(Text, nullable=False)

    created_at = Column(
        # DateTime,
        DateTime(timezone=True),
        server_default=func.now()
    )

    # ⭐ NEW FIELD (Phase 1 requirement)
    # generated_task_id = Column(
    #    Integer,
    #    ForeignKey("tasks.id"),
    #    nullable=True
    # )

    generated_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id"),
        nullable=True
    )

    sender = relationship(
        "User",
        back_populates="messages"
    )


# =========================
# TASKS
# =========================
class Task(Base):
    __tablename__ = "tasks"

    # id = Column(Integer, primary_key=True, index=True)
    id = Column(UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, index=True)

    title = Column(Text, nullable=False)
    description = Column(Text)

    creator_id = Column(
        # Integer,
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    start_time = Column(DateTime(timezone=True))
    remind_time = Column(DateTime(timezone=True))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # ⭐ NEW FIELD
    status = Column(
        String(20),
        default="Đang chờ"
    )

    source_message_id = Column(
        # Integer,
        UUID(as_uuid=True),
        ForeignKey("messages.id")
    )

    creator = relationship(
        "User",
        back_populates="created_tasks"
    )

    assignees = relationship(
        "TaskAssignee",
        cascade="all, delete-orphan",
        back_populates="task"
    )


# =========================
# TASK ASSIGNEES
# =========================
class TaskAssignee(Base):
    __tablename__ = "task_assignees"

    # id = Column(Integer, primary_key=True)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    task_id = Column(
        # Integer,
        UUID(as_uuid=True),
        ForeignKey("tasks.id"),
        nullable=False
    )

    user_id = Column(
        # Integer,
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    task = relationship(
        "Task",
        back_populates="assignees"
    )

    user = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            "task_id",
            "user_id",
            name="uq_task_user"
        ),
    )
