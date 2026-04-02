from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# DATABASE_URL = "postgresql://postgres:123@localhost:5434/task_schedule"
# DATABASE_URL = "postgresql://task_schedule_user:HSMfkigbqhS1SRY1YelIWVBwr5O0vZYV@dpg-d60lsenfte5s73b88430-a/task_schedule"
# DATABASE_URL = "postgresql://task_schedule_eibr_user:XAqJzuU6edO7VkD8qeP6RtIUlVwnKlOY@dpg-d75nv5u3jp1c73dg5mv0-a.oregon-postgres.render.com/task_schedule_eibr"
DATABASE_URL = "postgresql://task_schedule_4baw_user:jGm9uXRKbriCBDIjIMKk1I0sQ8GXDBti@dpg-d773fpuslomc73angs70-a.oregon-postgres.render.com/task_schedule_4baw"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
