from core.database import execute_query, get_db_connection, release_db_connection
from fastapi import HTTPException, status

class LikeService:
    @staticmethod
    def toggle_like(post_id: int, current_user_id: int):
        """Переключает лайк: добавляет/удаляет. Возвращает статус и счетчик"""
        post_check = execute_query(
            "SELECT id FROM posts WHERE id = %s", 
            (post_id,), 
            fetch=True
        )
        if not post_check:
            raise HTTPException(status_code=404, detail="Пост не найден")

        # есть ли уже лайк
        existing_like = execute_query(
            "SELECT 1 FROM likes WHERE user_id = %s AND post_id = %s", 
            (current_user_id, post_id), 
            fetch=True
        )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        conn.set_client_encoding("KOI8R")
        
        try:
            if existing_like:
                # УДАЛЯЕМ лайк
                cursor.execute(
                    "DELETE FROM likes WHERE user_id = %s AND post_id = %s",
                    (current_user_id, post_id)
                )
                action = "removed"
            else:
                # ДОБАВЛЯЕМ лайк
                cursor.execute(
                    "INSERT INTO likes (user_id, post_id) VALUES (%s, %s)",
                    (current_user_id, post_id)
                )
                action = "added"
            
            conn.commit()
            
            # Считаем лайки
            cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = %s", (post_id,))
            likes_count = cursor.fetchone()[0]
            
            return {
                "action": action, 
                "likes_count": likes_count,
                "message": f"Лайк {action}"
            }
            
        except Exception as e:
            conn.rollback()
            print(f"Ошибка лайка: {e}")
            raise HTTPException(status_code=500, detail="Ошибка обработки лайка")
        finally:
            cursor.close()
            release_db_connection(conn)

    @staticmethod
    def get_post_likes_count(post_id: int):
        """Количество лайков на пост"""
        result = execute_query(
            "SELECT COUNT(*) FROM likes WHERE post_id = %s",
            (post_id,),
            fetch=True
        )
        return result[0][0] if result else 0

    @staticmethod
    def is_user_liked_post(user_id: int, post_id: int):
        """Лайкнул ли пользователь пост"""
        result = execute_query(
            "SELECT 1 FROM likes WHERE user_id = %s AND post_id = %s",
            (user_id, post_id),
            fetch=True
        )
        return bool(result)
