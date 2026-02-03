from sqlalchemy.orm import Session
from app.models import Message, Task, TaskAssignee, User


def create_message(db: Session, sender_id: int, content: str):
    msg = Message(sender_id=sender_id, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def create_task(db: Session, data: dict, creator_id: int, message_id: int):
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

    for username in data.get("assignees", []):
        user = get_user_by_username(db, username)
        if user:
            db.add(TaskAssignee(task_id=task.id, user_id=user.id))

    db.commit()
    return task
