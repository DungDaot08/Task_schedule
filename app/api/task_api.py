from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Task
from app.schemas import TaskOut

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    return (
        db.query(Task)
        .options(joinedload(Task.assignees))
        .order_by(Task.created_at.desc())
        .all()
    )
