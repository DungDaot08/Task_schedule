from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth.security import verify_password, create_access_token
from pydantic import BaseModel


router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        raise HTTPException(401, "Invalid credentials")

    #if not verify_password(data.password, user.password):
        #raise HTTPException(401, "Invalid credentials")

    token = create_access_token(
        {
            "user_id": str(user.id),
            "username": user.username,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
        }
    }
