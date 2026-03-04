from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# DATABASE_URL = "postgresql://postgres:123@localhost:5434/task_schedule"
# DATABASE_URL = "postgresql://task_schedule_user:HSMfkigbqhS1SRY1YelIWVBwr5O0vZYV@dpg-d60lsenfte5s73b88430-a/task_schedule"
# DATABASE_URL = "postgresql://task_schedule_user:HSMfkigbqhS1SRY1YelIWVBwr5O0vZYV@dpg-d60lsenfte5s73b88430-a.oregon-postgres.render.com/task_schedule"
DATABASE_URL = "postgresql://task_schedule_satq_user:Fy39aEKuJHx1G8iUzhHQ4MGytt4W0Z6l@dpg-d6k48si4d50c73daabb0-a.oregon-postgres.render.com/task_schedule_satq"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
