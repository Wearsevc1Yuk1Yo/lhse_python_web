from .post import Post, next_post_id, posts_db
from .user import User, next_user_id, users_db

__all__ = ["User", "users_db", "next_user_id", "Post", "posts_db", "next_post_id"]
