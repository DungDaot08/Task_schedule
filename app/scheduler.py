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


def schedule_task_reminder_1(task_id: int, user_id: int, run_time: datetime):
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


def load_jobs_from_db_old():
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


def schedule_task_reminder(
    task_id: int,
    user_id: int,
    run_time: datetime,
    description: str,
    type: str    # 👈 mặc định
):
    """
    Schedule notify khi tới giờ
    """

    # ❗ tránh schedule trong quá khứ
    if run_time <= datetime.now(run_time.tzinfo):
        return

    def job():
        print(f"[SCHEDULER] Trigger task {task_id} - {type}")

        try:
            if type == "remind":
                msg = "Sắp đến giờ task"
            else:
                msg = "Task bắt đầu"

            asyncio.run(
                manager.send_to_user(
                    user_id,
                    {
                        "type": "task_reminder",
                        "task_id": task_id,
                        "reminder_type": type,  # type = 'remind' or 'start'
                        "description": description,
                        "message": msg  # "Sắp đến giờ task" or "Task bắt đầu"
                    }
                )
            )
        except Exception as e:
            print("WebSocket send error:", e)

    scheduler.add_job(
        job,
        "date",
        run_date=run_time,
        id=f"task_{task_id}_{user_id}_{type}",  # 👈 tránh bị overwrite
        replace_existing=True
    )


def load_jobs_from_db():
    db: Session = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        tasks = (
            db.query(Task)
            .filter(Task.start_time != None)
            .all()
        )

        count = 0

        for task in tasks:
            user_ids = [task.creator_id]

            assignees = (
                db.query(TaskAssignee)
                .filter(TaskAssignee.task_id == task.id)
                .all()
            )
            user_ids += [a.user_id for a in assignees]

            # 👇 schedule REMIND (nếu còn hạn)
            if task.remind_time and task.remind_time > now:
                for user_id in user_ids:
                    schedule_task_reminder(
                        task_id=task.id,
                        user_id=user_id,
                        run_time=task.remind_time,
                        description=task.description,
                        type="remind"
                    )
                count += 1

            # 👇 schedule START (nếu còn hạn)
            if task.start_time and task.start_time > now:
                for user_id in user_ids:
                    schedule_task_reminder(
                        task_id=task.id,
                        user_id=user_id,
                        run_time=task.start_time,
                        description=task.description,
                        type="start"
                    )
                count += 1

        print(f"[SCHEDULER] Loaded {count} jobs")

    finally:
        db.close()
