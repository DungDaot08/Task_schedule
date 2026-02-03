from fastapi import APIRouter
from app.ai.worker_render import run_once

router = APIRouter(prefix="/worker", tags=["worker"])


@router.post("/run")
def run_worker():
    return run_once()
