from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models import User
from app.auth.security import SECRET_KEY, ALGORITHM

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 🔥 FIX QUAN TRỌNG
        user_id = UUID(user_id)

    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
