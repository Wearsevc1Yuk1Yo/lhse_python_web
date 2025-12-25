from fastapi import APIRouter, HTTPException, status, Request
from services.like_service import LikeService

router = APIRouter(prefix="/api/likes", tags=["likes"])

@router.post("/posts/{post_id}/toggle")
async def toggle_post_like(request: Request, post_id: int):
    """Переключить лайк на посте (требует авторизации через session)"""

    session = request.session
    current_user_id = session.get("user_id")
    
    if not current_user_id:
        raise HTTPException(
            status_code=401, 
            detail="Требуется авторизация. Войдите в аккаунт."
        )
    
    return LikeService.toggle_like(post_id, current_user_id)

@router.get("/posts/{post_id}/count")
async def get_post_likes_count(post_id: int):
    """Получить количество лайков поста (public)"""
    return {"likes_count": LikeService.get_post_likes_count(post_id)}

@router.get("/posts/{post_id}/is-liked")
async def check_if_user_liked(request: Request, post_id: int):
    """Проверить, лайкнул ли текущий пользователь пост"""
    session = request.session
    current_user_id = session.get("user_id")
    
    if not current_user_id:
        return {"is_liked": False}
    
    return {"is_liked": LikeService.is_user_liked_post(current_user_id, post_id)}
