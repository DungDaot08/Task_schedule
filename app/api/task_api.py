from fastapi import Query
from sqlalchemy.orm import selectinload
from app.auth.deps import get_current_user
from app.models import Task, TaskAssignee
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.scheduler import (
    schedule_task_reminder,
    remove_all_task_schedules
)

from app.database import get_db
from app.models import Task
from app.schemas import TaskOut


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/old")
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


@router.get("")
def get_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tasks = (
        db.query(Task)
        .options(
            selectinload(Task.creator),  # load creator
            selectinload(Task.assignees).selectinload(
                TaskAssignee.user)  # load assignees + user
        )
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

    result = []

    for task in tasks:
        result.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "start_time": task.start_time,
            "remind_time": task.remind_time,
            "created_at": task.created_at,
            "status": task.status,

            "creator": {
                "user_id": task.creator.id,
                "username": task.creator.username
            } if task.creator else None,

            "assignees": [
                {
                    "user_id": a.user.id,
                    "username": a.user.username
                }
                for a in task.assignees
            ]
        })

    return result


@router.get("/by-status-old")
def get_tasks_by_status(
    status: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if status not in ["pending", "accepted", "completed"]:
        return {"error": "Status không hợp lệ"}

    tasks = (
        db.query(Task)
        .outerjoin(TaskAssignee)
        .filter(
            Task.status == status,
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


@router.get("/by-status")
def get_tasks_by_status(
    status: str = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if status not in ["pending", "accepted", "completed"]:
        return {"error": "Status không hợp lệ"}

    tasks = (
        db.query(Task)
        .options(
            selectinload(Task.creator),
            selectinload(Task.assignees).selectinload(TaskAssignee.user)
        )
        .outerjoin(TaskAssignee)
        .filter(
            Task.status == status,
            or_(
                Task.creator_id == current_user.id,
                TaskAssignee.user_id == current_user.id
            )
        )
        .distinct()
        .order_by(Task.id.desc())
        .all()
    )

    result = []

    for task in tasks:
        result.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "start_time": task.start_time,
            "remind_time": task.remind_time,
            "created_at": task.created_at,
            "status": task.status,

            "creator": {
                "user_id": task.creator.id,
                "username": task.creator.username
            } if task.creator else None,

            "assignees": [
                {
                    "user_id": a.user.id,
                    "username": a.user.username
                }
                for a in task.assignees
            ]
        })

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

    if task.creator_id != current_user.id:
        return {"error": "Không có quyền xóa task"}

    # 👇 lấy user_ids (creator + assignees)
    assignees = db.query(TaskAssignee).filter(
        TaskAssignee.task_id == task_id
    ).all()

    user_ids = [task.creator_id] + [a.user_id for a in assignees]

    # ✅ remove schedule
    remove_all_task_schedules(task.id, user_ids)

    # xóa assignees
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

    # 👇 lấy assignees
    assignees = db.query(TaskAssignee).filter(
        TaskAssignee.task_id == task.id
    ).all()

    user_ids = [task.creator_id] + [a.user_id for a in assignees]

    # ===== update fields =====
    if "title" in data:
        task.title = data["title"]

    if "description" in data:
        task.description = data["description"]

    if "start_time" in data:
        task.start_time = data["start_time"]

    if "remind_time" in data:
        task.remind_time = data["remind_time"]

    if "status" in data:
        if data["status"] not in ["pending", "accepted", "completed"]:
            return {"error": "Status không hợp lệ"}
        task.status = data["status"]

    remove_all_task_schedules(task.id, user_ids)

    db.commit()
    db.refresh(task)

    # ✅ chỉ xử lý schedule khi status = accepted
    if task.status == "accepted":

        # ✅ schedule lại
        for user_id in user_ids:
            if task.remind_time:
                schedule_task_reminder(
                    task_id=task.id,
                    user_id=user_id,
                    run_time=task.remind_time,
                    description=task.description,
                    type="remind"
                )

            if task.start_time:
                schedule_task_reminder(
                    task_id=task.id,
                    user_id=user_id,
                    run_time=task.start_time,
                    description=task.description,
                    type="start"
                )

    return {"message": "Cập nhật thành công", "task_id": task.id}
