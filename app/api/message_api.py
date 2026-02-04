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


@router.post("/messages", response_model=MessageOut)
def send_message(
    data: MessageCreate,
    background_tasks: BackgroundTasks,   # ⭐ thêm
    db: Session = Depends(get_db)
):
    # 1️⃣ Tạo message
    msg = create_message(db, data.sender_id, data.content)

    # 2️⃣ Push queue
    push_job(msg.id)

    # 3️⃣ Trigger worker background
    background_tasks.add_task(run_once)

    return msg
