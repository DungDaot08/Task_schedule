from app.auth.deps import get_current_user
from app.models import Task, TaskAssignee
from sqlalchemy import or_
from sqlalchemy.orm import Session
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


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("")
def get_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    tasks = (
        db.query(Task)
        .outerjoin(TaskAssignee)
        .filter(
            or_(
                Task.creator_id == current_user.id,
                TaskAssignee.user_id == current_user.id
            )
        )
        .distinct()
        .all()
    )

    return tasks
