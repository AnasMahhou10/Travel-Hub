import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_redis

router = APIRouter(tags=["auth"])

SESSION_TTL = 900


class LoginRequest(BaseModel):
    userId: str


@router.post("/login")
async def login(body: LoginRequest):
    if not body.userId:
        raise HTTPException(status_code=400, detail="userId requis")

    token = str(uuid.uuid4())
    redis = get_redis()
    await redis.set(f"session:{token}", body.userId, ex=SESSION_TTL)

    return {"token": token, "expires_in": SESSION_TTL}


@router.get("/session/{token}")
async def verify_session(token: str):
    redis = get_redis()
    user_id = await redis.get(f"session:{token}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Session invalide ou expirée")

    return {"userId": user_id, "valid": True}