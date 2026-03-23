from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database import get_db
from app.schemas import MessageCreate, MessageOut
from app.models import Message
from app.auth.deps import get_current_user
from app.ai.worker_render import run_once
from app.task_queue.redis_queue import push_job

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.post("", response_model=MessageOut)
def send_message(
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

    push_job(msg.id)

    background_tasks.add_task(run_once)

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


@router.get("/{message_id}", response_model=MessageOut)
def get_message(message_id: int, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return message
