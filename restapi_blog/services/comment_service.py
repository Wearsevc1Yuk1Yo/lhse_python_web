# from datetime import datetime

from core.database import execute_query
from fastapi import HTTPException, status


class CommentService:
    @staticmethod
    async def create_comment(comment_data, current_user_id):
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
