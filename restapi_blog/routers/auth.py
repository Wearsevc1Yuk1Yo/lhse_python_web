from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse
from schemas.user import UserCreate, UserResponse
from services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    try:
        return await UserService.create_user(user)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Регистрация ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка регистрации")
