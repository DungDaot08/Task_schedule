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

    from app.models import User

    result = []

    for task in tasks:
        assignees = (
            db.query(TaskAssignee, User)
            .join(User, TaskAssignee.user_id == User.id)
            .filter(TaskAssignee.task_id == task.id)
            .all()
        )

        task_data = task.__dict__.copy()
        task_data.pop("_sa_instance_state", None)

        task_data["assignees"] = [
            {
                "user_id": a.user_id,
                "username": u.username
            }
            for a, u in assignees
        ]

        result.append(task_data)

    return result
