from core.database import execute_query

class FavoritesService:
    @staticmethod
    def toggle_favorite(user_id: int, post_id: int):
        """Добавить/убрать из избранного"""
        # Проверяем наличие
        exists = execute_query("""
            SELECT 1 FROM favorites WHERE user_id = %s AND post_id = %s
        """, (user_id, post_id), fetch=True)
        
        if exists:
            execute_query("""
                DELETE FROM favorites WHERE user_id = %s AND post_id = %s
            """, (user_id, post_id))
            action = "removed"
        else:
            execute_query("""
                INSERT INTO favorites (user_id, post_id) VALUES (%s, %s)
            """, (user_id, post_id))
            action = "added"
        
        count = FavoritesService.get_post_count(post_id)
        return {"action": action, "favorites_count": count}

    @staticmethod
    def get_post_count(post_id: int):
        result = execute_query("SELECT COUNT(*) FROM favorites WHERE post_id = %s", (post_id,), fetch=True)
        return result[0][0] if result else 0

    @staticmethod
    def is_favorited(user_id: int, post_id: int):
        result = execute_query("""
            SELECT 1 FROM favorites WHERE user_id = %s AND post_id = %s
        """, (user_id, post_id), fetch=True)
        return bool(result)

    @staticmethod
    def get_user_favorites(user_id: int):
        result = execute_query("""
            SELECT p.id, p.title, p.content, p.created_at, u.username
            FROM favorites f
            JOIN posts p ON f.post_id = p.id AND p.is_published = true
            JOIN users u ON p.user_id = u.id
            WHERE f.user_id = %s
            ORDER BY f.created_at DESC
        """, (user_id,), fetch=True)
        return [{
            "id": r[0], "title": r[1], 
            "content": r[2][:100] + "..." if len(r[2]) > 100 else r[2],
            "created_at": r[3].isoformat(), "author_name": r[4]
        } for r in result]
