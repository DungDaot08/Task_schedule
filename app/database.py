from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# DATABASE_URL = "postgresql://postgres:123@localhost:5434/task_schedule"
DATABASE_URL = "postgresql://task_schedule_user:HSMfkigbqhS1SRY1YelIWVBwr5O0vZYV@dpg-d60lsenfte5s73b88430-a/task_schedule"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
