from core.database import execute_query

class ProfileService:
    @staticmethod
    def get_profile(user_id: int):
        """Получить профиль пользователя"""
        result = execute_query("""
            SELECT id, username, email, age, hobbies, bio, avatar_url, created_at
            FROM users WHERE id = %s
        """, (user_id,), fetch=True)
        
        if result:
            row = result[0]
            return {
                "id": row[0], "username": row[1], "email": row[2],
                "age": row[3], "hobbies": row[4] or "", "bio": row[5] or "",
                "avatar_url": row[6], "created_at": row[7].isoformat()
            }
        return None

    @staticmethod
    def update_profile(user_id: int, age: int = None, hobbies: str = None, bio: str = None, avatar_url: str = None):
        """Обновить профиль"""
        updates = []
        params = []
        
        if age is not None:
            updates.append("age = %s")
            params.append(age)
        if hobbies is not None:
            updates.append("hobbies = %s")
            params.append(hobbies)
        if bio is not None:
            updates.append("bio = %s")
            params.append(bio)
        if avatar_url is not None:
            updates.append("avatar_url = %s")
            params.append(avatar_url)
        
        if not updates:
            return False
        
        params.append(user_id)
        query = f"""
            UPDATE users SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        execute_query(query, params)
        return True
