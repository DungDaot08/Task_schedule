from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import MessageCreate, MessageOut
from app.crud import create_message
from app.task_queue.redis_queue import push_job

router = APIRouter()


@router.post("/messages", response_model=MessageOut)
def send_message(data: MessageCreate, db: Session = Depends(get_db)):
    msg = create_message(db, data.sender_id, data.content)
    push_job(msg.id)
    return msg
