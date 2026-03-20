# from app.scheduler import schedule_task_reminder
from app.database import SessionLocal
from app.models import Task, TaskAssignee
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from datetime import datetime, timezone
import asyncio

from app.ws.manager import manager

scheduler = BackgroundScheduler()


def start_scheduler():
    scheduler.start()


def schedule_task_reminder(task_id: int, user_id: int, run_time: datetime):
    """
    Schedule notify khi tới giờ
    """

    def job():
        print(f"[SCHEDULER] Trigger task {task_id}")

        try:
            asyncio.run(
                manager.send_to_user(
                    user_id,
                    {
                        "type": "task_reminder",
                        "task_id": task_id,
                        "message": "Bạn có task đến giờ!"
                    }
                )
            )
        except Exception as e:
            print("WebSocket send error:", e)

    scheduler.add_job(
        job,
        "date",
        run_date=run_time,
        id=f"task_{task_id}_{user_id}",
        replace_existing=True
    )


def load_jobs_from_db():
    db: Session = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        tasks = (
            db.query(Task)
            .filter(
                (Task.start_time != None) &
                (Task.start_time > now)
            )
            .all()
        )

        for task in tasks:
            run_time = task.remind_time or task.start_time

            if not run_time or run_time <= now:
                continue

            # 👤 creator
            schedule_task_reminder(task.id, task.creator_id, run_time)

            # 👥 assignees
            assignees = (
                db.query(TaskAssignee)
                .filter(TaskAssignee.task_id == task.id)
                .all()
            )

            for a in assignees:
                schedule_task_reminder(task.id, a.user_id, run_time)

        print(f"[SCHEDULER] Loaded {len(tasks)} tasks")

    finally:
        db.close()
