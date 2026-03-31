from sqlalchemy.orm import Session
from app.models import Message, Task, TaskAssignee, User
from app.scheduler import schedule_task_reminder
from uuid import UUID


def create_message(db: Session, sender_id: UUID, content: str):
    msg = Message(sender_id=sender_id, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def create_task(db: Session, data: dict, creator_id: UUID, message_id: UUID):
    task = Task(
        title=data["title"],
        description=data.get("description"),
        start_time=data.get("start_time"),
        remind_time=data.get("remind_time"),
        creator_id=creator_id,
        source_message_id=message_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    assignee_ids = []

    # tạo assignees
    for username in data.get("assignees", []):
        user = get_user_by_username(db, username)
        if user:
            db.add(TaskAssignee(task_id=task.id, user_id=user.id))
            assignee_ids.append(user.id)

    db.commit()

    # 🔥 SCHEDULER
    user_ids = [creator_id] + assignee_ids

    return task, assignee_ids
