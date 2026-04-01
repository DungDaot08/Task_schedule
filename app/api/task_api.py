from fastapi import Query
from sqlalchemy.orm import selectinload
from app.auth.deps import get_current_user
from app.models import Task, TaskAssignee, Message
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.scheduler import (
    schedule_task_reminder,
    remove_all_task_schedules
)
from uuid import UUID
from app.database import get_db
from app.models import Task
from app.schemas import TaskOut
from app.task_queue.redis_queue import publish_event

router = APIRouter(prefix="/tasks", tags=["Tasks"])


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
        .order_by(Task.created_at.desc())
        .all()
    )

    result = []

    for task in tasks:
        result.append({
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "start_time": task.start_time,
            "remind_time": task.remind_time,
            "created_at": task.created_at,
            "status": task.status,

            "creator": {
                "user_id": str(task.creator.id),
                "username": task.creator.username
            } if task.creator else None,

            "assignees": [
                {
                    "user_id": str(a.user.id),
                    "username": a.user.username
                }
                for a in task.assignees
            ]
        })

    return result


@router.get("/by-status")
def get_tasks_by_status(
    status: str = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if status not in ["Đang chờ", "Đã xác nhận", "Hoàn thành"]:
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
        .order_by(Task.created_at.desc())
        .all()
    )

    result = []

    for task in tasks:
        result.append({
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "start_time": task.start_time,
            "remind_time": task.remind_time,
            "created_at": task.created_at,
            "status": task.status,

            "creator": {
                "user_id": str(task.creator.id),
                "username": task.creator.username
            } if task.creator else None,

            "assignees": [
                {
                    "user_id": str(a.user.id),
                    "username": a.user.username
                }
                for a in task.assignees
            ]
        })

    return result


@router.delete("/{task_id}")
def delete_task(
    task_id: UUID,
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

    for uid in user_ids:
        publish_event({
            "type": "task_deleted",
            "user_ids": str(uid),  # 👈 nhiều user
            "data": {
                "task_id": str(task.id)
            }
        })

    # ✅ remove schedule
    # remove_all_task_schedules(task.id, user_ids)
    remove_all_task_schedules(
        str(task.id),
        [str(uid) for uid in user_ids]
    )

    # clear FK trước
    db.query(Message).filter(
        Message.generated_task_id == task.id
    ).update(
        {Message.generated_task_id: None},
        synchronize_session=False
    )

    # xóa assignees
    db.query(TaskAssignee).filter(
        TaskAssignee.task_id == task_id
    ).delete()

    db.flush()  # 👈 cực kỳ quan trọng

    # xóa task
    db.delete(task)

    db.commit()

    return {"message": "Xóa task thành công"}


@router.patch("/{task_id}")
def update_task(
    task_id: UUID,
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
        if data["status"] not in ["Đang chờ", "Đã chấp nhận", "Hoàn thành"]:
            return {"error": "Status không hợp lệ"}
        task.status = data["status"]

    # remove_all_task_schedules(task.id, user_ids)
    remove_all_task_schedules(
        str(task.id),
        [str(uid) for uid in user_ids]
    )

    db.commit()
    db.refresh(task)

    payload = {
        "task_id": str(task.id),
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "start_time": str(task.start_time) if task.start_time else None,
        "remind_time": str(task.remind_time) if task.remind_time else None,
    }

    for uid in user_ids:
        publish_event({
            "type": "task_updated",
            "user_id": str(uid),
            "data": payload
        })

    # ✅ chỉ xử lý schedule khi status = accepted
    if task.status == "Đã chấp nhận":

        # ✅ schedule lại
        for user_id in user_ids:
            if task.remind_time:
                schedule_task_reminder(
                    task_id=str(task.id),
                    user_id=str(user_id),
                    run_time=task.remind_time,
                    description=task.description,
                    type="remind"
                )

            if task.start_time:
                schedule_task_reminder(
                    task_id=str(task.id),
                    user_id=str(user_id),
                    run_time=task.start_time,
                    description=task.description,
                    type="start"
                )

    return {"message": "Cập nhật thành công", "task_id": task.id}
