# from datetime import datetime

from core.database import execute_query
from fastapi import HTTPException, status
from schemas.post import PostCreate, PostUpdate
from services.like_service import LikeService


class PostService:
    @staticmethod
    async def create_post(post_data: PostCreate, current_user_id: int):
        # существование автора
        author = execute_query(
            "SELECT id FROM users WHERE id = %s", (current_user_id,), fetch=True
        )
        if not author:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Автор не найден"
            )

        # Проверка заголовка
        if not post_data.title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Заголовок не может быть пустым",
            )

        # Проверка содержания
        if not post_data.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Содержание не может быть пустым",
            )

        # Создаем пост
        try:
            result = execute_query(
                """
                INSERT INTO posts (user_id, title, content)
                VALUES (%s, %s, %s)
                RETURNING id, user_id, title, content, created_at, updated_at
            """,
                (current_user_id, post_data.title.strip(), post_data.content.strip()),
                fetch=True,
            )

            post = result[0]
            return {
                "id": post[0],
                "author_id": post[1],
                "title": post[2],
                "content": post[3],
                "created_at": post[4].isoformat(),
                "updated_at": post[5].isoformat(),
            }
        except Exception as e:
            print(f"Ошибка создания поста: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка создания поста",
            )

    @staticmethod
    async def get_all_posts(skip: int = 0, limit: int = 10, search_query: str = None):
        try:
            if search_query:
                search_term = f"%{search_query}%"
                query = """
                    SELECT p.id, p.user_id, p.title, p.content, p.created_at, p.updated_at, u.username
                    FROM posts p JOIN users u ON p.user_id = u.id
                    WHERE p.title ILIKE %s OR p.content ILIKE %s
                    ORDER BY p.created_at DESC LIMIT %s OFFSET %s
                """
                params = (search_term, search_term, limit, skip)
            else:
                query = """
                    SELECT p.id, p.user_id, p.title, p.content, p.created_at, p.updated_at, u.username
                    FROM posts p JOIN users u ON p.user_id = u.id
                    ORDER BY p.created_at DESC LIMIT %s OFFSET %s
                """
                params = (limit, skip)

            posts = execute_query(query, params, fetch=True)
            result = []
            for post in posts:
                content_preview = (
                    post[3][:100] + "..." if len(post[3]) > 100 else post[3]
                )
                result.append(
                    {
                        "id": post[0],
                        "author_id": post[1],
                        "title": post[2],
                        "content_preview": content_preview,
                        "created_at": post[4].isoformat(),
                        "updated_at": post[5].isoformat(),
                        "author_name": post[6],
                    }
                )
            return result
        except Exception as e:
            print(f"Ошибка получения постов: {e}")
            raise HTTPException(status_code=500, detail="Ошибка получения постов")


    # глав цаца все изменения сюда
    @staticmethod
    async def get_post(post_id: int, current_user_id: int = None):
        post = execute_query(
            """
            SELECT p.id, p.user_id, p.title, p.content, p.is_published,
                p.created_at, p.updated_at, u.username as author_name
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = %s
        """,
            (post_id,),
            fetch=True,
        )

        if not post:
            raise HTTPException(status_code=404, detail="Пост не найден")

        post = post[0]

        comments = execute_query(
            """
            SELECT c.id, c.user_id, u.username, c.content, c.created_at,
                c.parent_comment_id
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = %s
            ORDER BY c.created_at ASC
        """,
            (post_id,),
            fetch=True,
        )

        likes_count = LikeService.get_post_likes_count(post_id)
        is_liked = False  
        if current_user_id:
            is_liked = LikeService.is_user_liked_post(current_user_id, post_id)  
        
        favorites_count = 0
        is_favorited = False
        try:
            from services.favorites_service import FavoritesService
            favorites_count = FavoritesService.get_post_count(post_id)
            if current_user_id:
                is_favorited = FavoritesService.is_favorited(current_user_id, post_id)
        except:
            pass
        
        return {
            "id": post[0],
            "author_id": post[1],
            "title": post[2],
            "content": post[3],
            "is_published": post[4],
            "created_at": post[5],
            "updated_at": post[6],
            "author_name": post[7],
            "likes_count": likes_count,
            "is_liked": is_liked,
            "favorites_count": favorites_count,
            "is_favorited": is_favorited,
            "comments": comments,
        }

    @staticmethod
    async def update_post(post_id: int, post_data: PostUpdate, current_user_id: int):
        # Сначала проверяем, существует ли пост
        post = await PostService.get_post(post_id)

        # Проверяем права доступа - можно обновлять только свой пост
        if post["author_id"] != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы можете редактировать только свои посты",
            )

        update_fields = []
        params = []

        if post_data.title is not None and post_data.title.strip():
            update_fields.append("title = %s")
            params.append(post_data.title.strip())

        if post_data.content is not None and post_data.content.strip():
            update_fields.append("content = %s")
            params.append(post_data.content.strip())

        if not update_fields:
            return post

        params.append(post_id)

        try:
            query = f"""
                UPDATE posts
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, user_id, title, content, created_at, updated_at
            """

            result = execute_query(query, tuple(params), fetch=True)

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Пост не найден"
                )

            post = result[0]
            return {
                "id": post[0],
                "author_id": post[1],
                "title": post[2],
                "content": post[3],
                "created_at": post[4].isoformat(),
                "updated_at": post[5].isoformat(),
            }
        except Exception as e:
            print(f"Ошибка обновления поста: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка обновления поста",
            )

    @staticmethod
    async def delete_post(post_id: int, current_user_id: int):
        # Сначала проверяем, существует ли пост
        post = await PostService.get_post(post_id)

        # Проверяем права доступа - можно удалять только свой пост
        if post["author_id"] != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы можете удалять только свои посты",
            )

        try:
            # Удаляем связанные комментарии
            execute_query(
                """
                DELETE FROM comments WHERE post_id = %s
            """,
                (post_id,),
            )

            # Удаляем из избранного
            execute_query(
                """
                DELETE FROM favorites WHERE post_id = %s
            """,
                (post_id,),
            )

            # Удаляем связи с категориями
            execute_query(
                """
                DELETE FROM post_categories WHERE post_id = %s
            """,
                (post_id,),
            )

            # Удаляем сам пост
            execute_query(
                """
                DELETE FROM posts WHERE id = %s
            """,
                (post_id,),
            )

            return {"message": f"Пост с ID {post_id} успешно удален"}
        except Exception as e:
            print(f"Ошибка удаления поста: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка удаления поста: {str(e)}",
            )

    @staticmethod
    async def search_posts(query: str, skip: int = 0, limit: int = 10):
        """Поиск постов по заголовку и содержанию"""
        return await PostService.get_all_posts(
            skip=skip, limit=limit, search_query=query
        )
