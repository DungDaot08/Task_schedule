from fastapi import Query
from app.models import Message, User
from app.ws.manager import manager  # nhớ import
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database import get_db
from app.schemas import MessageCreate, MessageOut
from app.models import Message
from app.auth.deps import get_current_user
from app.ai.worker_render import run_once
from app.task_queue.redis_queue import push_job
import uuid
import os

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.post("", response_model=MessageOut)
async def send_message(
    data: MessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    msg = Message(
        sender_id=current_user.id,
        content=data.content
    )

    db.add(msg)
    db.commit()
    db.refresh(msg)

    # ✅ push WS realtime

    def to_dict(obj):
        return {
            # convert hết sang string cho chắc
            c.name: str(getattr(obj, c.name))
            if isinstance(getattr(obj, c.name), uuid.UUID)
            else getattr(obj, c.name)
            for c in obj.__table__.columns
        }

    await manager.broadcast({
        "type": "new_message",
        "data": {
            **to_dict(msg),
            "username": current_user.username
        }
    })

    # push_job(msg.id)
    push_job(str(msg.id))
    await run_once()  # 👈 chạy cùng process
    print("🔥 SEND MESSAGE PID:", os.getpid())

    return msg


@router.get("", response_model=list[MessageOut])
def list_messages(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    return (
        db.query(Message)
        .filter(Message.sender_id == current_user.id)
        .order_by(Message.created_at.desc())
        .all()
    )


@router.get("/all")
def list_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Message, User.username)
        .join(User, User.id == Message.sender_id)
    )

    total = query.count()

    results = (
        query
        .order_by(Message.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    def to_dict(obj):
        return {
            c.name: str(getattr(obj, c.name))
            if isinstance(getattr(obj, c.name), uuid.UUID)
            else getattr(obj, c.name)
            for c in obj.__table__.columns
        }

    data = [
        {
            **to_dict(msg),
            "username": username
        }
        for msg, username in results
    ]

    return {
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        }
    }


@router.get("/{message_id}", response_model=MessageOut)
def get_message(message_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    message = db.query(Message).filter(Message.id == message_id).filter(
        Message.sender_id == current_user.id).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return message
