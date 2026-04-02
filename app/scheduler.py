# from app.scheduler import schedule_task_reminder
import pytz
from app.database import SessionLocal
from app.models import Task, TaskAssignee
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from datetime import datetime, timezone
import asyncio
from uuid import UUID
from app.ws.manager import manager
from app.task_queue.redis_queue import publish_event

scheduler = BackgroundScheduler(
    timezone=pytz.timezone("Asia/Ho_Chi_Minh")
)


def start_scheduler():
    scheduler.start()


def schedule_task_reminder_1(
    task_id: UUID,
    user_id: UUID,
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

            # asyncio.run(
                # manager.send_to_user(
                #    user_id,
                #    {
                #        "type": "task_reminder",
                #        "data": {
                #            "task_id": str(task_id),
                #            "reminder_type": type,   # 'remind' | 'start'
                #            "message": description,
                #            # "label": msg             # 👈 optional: text hiển thị
                #        }
                #    }
            #    )
                publish_event(
                    {
                        "type": "task_reminder",
                        "user_id": str(user_id),
                        "data": {
                            "task_id": str(task_id),
                            "reminder_type": type,   # 'remind' | 'start'
                            "message": description,
                            # "label": msg             # 👈 optional: text hiển thị
                        }
                    }
                )
            # )

        except Exception as e:
            print("WebSocket send error:", e)

    scheduler.add_job(
        job,
        "date",
        run_date=run_time,
        # id=f"task_{task_id}_{user_id}_{type}",  # 👈 tránh bị overwrite
        id=f"task_{str(task_id)}_{str(user_id)}_{type}",
        replace_existing=True
    )


def schedule_task_reminder(
    task_id,
    user_id,
    run_time,
    description,
    type
):
    tz = pytz.timezone("Asia/Ho_Chi_Minh")

    # ✅ đảm bảo có timezone
    if run_time.tzinfo is None:
        run_time = tz.localize(run_time)

    now = datetime.now(tz)

    if run_time <= now:
        print("⚠️ Skip job in the past")
        return

    def job():
        print(f"[SCHEDULER] Trigger task {task_id} - {type}")

        publish_event({
            "type": "task_reminder",
            "user_id": str(user_id),
            "data": {
                "task_id": str(task_id),
                "reminder_type": type,
                "message": description,
            }
        })

    scheduler.add_job(
        job,
        "date",
        run_date=run_time,
        id=f"task_{task_id}_{user_id}_{type}",
        replace_existing=True
    )


def load_jobs_from_db():
    db: Session = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        tasks = (
            db.query(Task)
            .filter(
                Task.start_time != None,
                Task.status == "Đã chấp nhận")
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
                        task_id=str(task.id),
                        user_id=str(user_id),
                        run_time=task.remind_time,
                        description=task.description,
                        type="remind"
                    )
                count += 1

            # 👇 schedule START (nếu còn hạn)
            if task.start_time and task.start_time > now:
                for user_id in user_ids:
                    schedule_task_reminder(
                        task_id=str(task.id),
                        user_id=str(user_id),
                        run_time=task.start_time,
                        description=task.description,
                        type="start"
                    )
                count += 1

        print(f"[SCHEDULER] Loaded {count} jobs")

    finally:
        db.close()


def remove_all_task_schedules(task_id, user_ids: list):
    for user_id in user_ids:
        for type in ["remind", "start"]:
            job_id = f"task_{str(task_id)}_{str(user_id)}_{type}"

            try:
                scheduler.remove_job(job_id)
                print(f"[SCHEDULER] Removed job {job_id}")
            except Exception:
                pass
