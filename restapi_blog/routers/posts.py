from fastapi import APIRouter
from schemas.post import PostCreate, PostUpdate
from services.post_service import PostService

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.post("/", response_model=None)
async def create_post(post: PostCreate):
    return await PostService.create_post(post)


@router.get("/", response_model=None)
async def get_posts():
    return await PostService.get_all_posts()


@router.get("/{post_id}", response_model=None)
async def get_post(post_id: int):
    return await PostService.get_post(post_id)


@router.put("/{post_id}", response_model=None)
async def update_post(post_id: int, post: PostUpdate):
    return await PostService.update_post(post_id, post)


@router.delete("/{post_id}")
async def delete_post(post_id: int):
    return await PostService.delete_post(post_id)
