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
        .order_by(Task.id)
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

        creator = db.query(User).filter(User.id == task.creator_id).first()

        task_data = task.__dict__.copy()
        task_data.pop("_sa_instance_state", None)

        # 👇 bỏ creator_id
        task_data.pop("creator_id", None)

        task_data["assignees"] = [
            {
                "user_id": a.user_id,
                "username": u.username
            }
            for a, u in assignees
        ]

        task_data["creator"] = {
            "user_id": creator.id,
            "username": creator.username
        } if creator else None

        result.append(task_data)

    return result


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        return {"error": "Task không tồn tại"}

    # 👇 chỉ cho creator xóa
    if task.creator_id != current_user.id:
        return {"error": "Không có quyền xóa task"}

    # xóa assignees trước
    db.query(TaskAssignee).filter(TaskAssignee.task_id == task_id).delete()

    # xóa task
    db.delete(task)
    db.commit()

    return {"message": "Xóa task thành công"}


@router.patch("/{task_id}")
def update_task(
    task_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        return {"error": "Task không tồn tại"}

    # 👇 chỉ creator được sửa
    if task.creator_id != current_user.id:
        return {"error": "Không có quyền chỉnh sửa task"}

    # ===== update fields =====
    if "title" in data:
        task.title = data["title"]

    if "description" in data:
        task.description = data["description"]

    if "start_time" in data:
        task.start_time = data["start_time"]

    if "remind_time" in data:
        task.remind_time = data["remind_time"]

    # 👇 thêm status
    if "status" in data:
        if data["status"] not in ["pending", "completed"]:
            return {"error": "Status không hợp lệ"}
        task.status = data["status"]

    db.commit()
    db.refresh(task)

    return {"message": "Cập nhật thành công", "task_id": task.id}
