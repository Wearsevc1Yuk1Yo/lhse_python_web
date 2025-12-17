from typing import Optional

from pydantic import BaseModel, validator


class PostCreate(BaseModel):
    author_id: int
    title: str
    content: str

    @validator("title")
    def title_length(cls, v):
        if not v.strip():
            raise ValueError("Заголовок не может быть пустым")
        return v.strip()

    @validator("content")
    def content_length(cls, v):
        if not v.strip():
            raise ValueError("Содержание не может быть пустым")
        return v.strip()


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

    @validator("title")
    def title_length(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Заголовок не может быть пустым")
        return v.strip() if v else v

    @validator("content")
    def content_length(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Содержание не может быть пустым")
        return v.strip() if v else v


class PostResponse(BaseModel):
    id: int
    author_id: int
    title: str
    content: str
    created_at: str
    updated_at: str
