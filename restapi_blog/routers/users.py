from fastapi import APIRouter
from schemas.user import UserCreate, UserResponse, UserUpdate
from services.user_service import UserService

# from fastapi import HTTPException


router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate):
    return await UserService.create_user(user)


@router.get("/", response_model=list[UserResponse])
async def get_users():
    return await UserService.get_all_users()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    return await UserService.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate):
    return await UserService.update_user(user_id, user)


@router.delete("/{user_id}")
async def delete_user(user_id: int):
    return await UserService.delete_user(user_id)
