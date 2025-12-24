# from datetime import datetime

from core.database import execute_query
from fastapi import HTTPException, status
from schemas.comment import CommentCreate


class CommentService:
    @staticmethod
    async def create_comment(comment_data: CommentCreate, current_user_id: int):
        # существование поста
        post = execute_query(
            "SELECT id FROM posts WHERE id = %s", (comment_data.post_id,), fetch=True
        )
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Пост не найден"
            )

        # Создаем комментарий
        try:
            print(
                f"💬 Создание комментария: user_id={current_user_id}, post_id={comment_data.post_id}"
            )
            result = execute_query(
                """
                INSERT INTO comments (user_id, post_id, parent_comment_id, content)
                VALUES (%s, %s, %s, %s)
                RETURNING id, user_id, post_id, content, created_at, updated_at
            """,
                (
                    current_user_id,
                    comment_data.post_id,
                    comment_data.parent_comment_id,
                    comment_data.content.strip(),
                ),
                fetch=True,
            )
            print(f"💬 Результат INSERT: {result}")

            comment = result[0]
            return {
                "id": comment[0],
                "user_id": comment[1],
                "post_id": comment[2],
                "content": comment[3],
                "created_at": comment[4].isoformat(),
                "updated_at": comment[5].isoformat(),
            }
        except Exception as e:
            print(f"Ошибка создания комментария: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка создания комментария",
            )

    @staticmethod
    async def get_comments_for_post(post_id: int):
        comments = execute_query(
            """
            SELECT c.id, c.user_id, u.username, c.content, c.created_at
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = %s
            ORDER BY c.created_at ASC
            """,
            (post_id,),
            fetch=True,
        )
        return [
            {
                "id": row[0],
                "user_id": row[1],
                "author_name": row[2],
                "content": row[3],
                "created_at": row[4].isoformat(),
            }
            for row in comments
        ]
