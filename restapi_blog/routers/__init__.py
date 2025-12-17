from .posts import router as posts_router
from .users import router as users_router

__all__ = ["users_router", "posts_router"]
