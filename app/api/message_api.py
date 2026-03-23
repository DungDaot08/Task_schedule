from fastapi import HTTPException
from app.schemas import MessageOut
from app.models import Message
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import MessageCreate, MessageOut
from app.crud import create_message
from app.task_queue.redis_queue import push_job
from app.ai.worker_render import run_once


router = APIRouter()


# @router.post("/messages", response_model=MessageOut)
# def send_message(data: MessageCreate, db: Session = Depends(get_db)):
#    msg = create_message(db, data.sender_id, data.content)
#    push_job(msg.id)
#    return msg


@router.get("/", response_model=list[MessageOut])
def list_messages(db: Session = Depends(get_db)):
    return (
        db.query(Message)
        .order_by(Message.created_at.desc())
        .all()
    )


@router.get("/{message_id}", response_model=MessageOut)
def get_message(message_id: int, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return message


@router.post("/messages", response_model=MessageOut)
def send_message(
    data: MessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    msg = create_message(db, data.sender_id, data.content)

    push_job(msg.id)

    # chạy background
    background_tasks.add_task(run_once)

    # 👇 chờ nhẹ (hack nhỏ)
    import time
    time.sleep(3)

    db.refresh(msg)

    return msg
