from typing import Optional

from pydantic import BaseModel, validator


class CommentCreate(BaseModel):
    post_id: int
    parent_comment_id: Optional[int] = None
    content: str

    @validator("content")
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Комментарий не может быть пустым")
        return v.strip()
