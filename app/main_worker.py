from fastapi import FastAPI
from app.api.run_worker import router as worker_router

app = FastAPI(title="AI Worker API")

app.include_router(worker_router)


@app.get("/")
def health():
    return {"status": "ok"}
