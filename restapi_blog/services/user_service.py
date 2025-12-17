from datetime import datetime

from core.database import execute_query
from fastapi import HTTPException, status
from passlib.context import CryptContext
from schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        # Для совместимости с существующими данными, где пароли не хешированы
        if hashed_password == plain_password:
            return True
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    async def create_user(user_data: UserCreate):
        # Проверка уникальности email
        existing_user = execute_query(
            "SELECT id FROM users WHERE email = %s", (user_data.email,), fetch=True
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует",
            )

        # Проверка уникальности логина
        existing_user = execute_query(
            "SELECT id FROM users WHERE username = %s", (user_data.login,), fetch=True
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким логином уже существует",
            )

        hashed_password = UserService.get_password_hash(user_data.password)

        try:
            result = execute_query(
                """
                INSERT INTO users (email, username, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id, email, username, created_at, updated_at
            """,
                (user_data.email, user_data.login, hashed_password),
                fetch=True,
            )

            user = result[0]
            return {
                "id": user[0],
                "email": user[1],
                "login": user[2],
                "created_at": user[3].isoformat(),
                "updated_at": user[4].isoformat(),
            }
        except Exception as e:
            print(f"Ошибка создания пользователя: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка создания пользователя",
            )

    @staticmethod
    async def get_all_users():
        try:
            users = execute_query(
                """
                SELECT id, email, username, created_at, updated_at
                FROM users
                ORDER BY created_at DESC
            """,
                fetch=True,
            )

            return [
                {
                    "id": user[0],
                    "email": user[1],
                    "login": user[2],
                    "created_at": user[3].isoformat()
                    if user[3]
                    else datetime.now().isoformat(),
                    "updated_at": user[4].isoformat()
                    if user[4]
                    else datetime.now().isoformat(),
                }
                for user in users
            ]
        except Exception as e:
            print(f"Ошибка получения пользователей: {e}")
            return []

    @staticmethod
    async def get_user(user_id: int):
        try:
            user = execute_query(
                """
                SELECT id, email, username, created_at, updated_at
                FROM users
                WHERE id = %s
            """,
                (user_id,),
                fetch=True,
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Пользователь не найден",
                )

            user = user[0]
            return {
                "id": user[0],
                "email": user[1],
                "login": user[2],
                "created_at": user[3].isoformat()
                if user[3]
                else datetime.now().isoformat(),
                "updated_at": user[4].isoformat()
                if user[4]
                else datetime.now().isoformat(),
            }
        except HTTPException:
            raise
        except Exception as e:
            print(f"Ошибка получения пользователя: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка получения пользователя",
            )

    @staticmethod
    async def update_user(user_id: int, user_data: UserUpdate):
        # Сначала проверяем, существует ли пользователь
        await UserService.get_user(user_id)

        update_fields = []
        params = []
        param_index = 1

        if user_data.email is not None:
            # Проверка уникальности email
            existing_user = execute_query(
                "SELECT id FROM users WHERE email = %s AND id != %s",
                (user_data.email, user_id),
                fetch=True,
            )
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email уже используется",
                )
            update_fields.append(f"email = ${param_index}")
            params.append(user_data.email)
            param_index += 1

        if user_data.login is not None:
            # Проверка уникальности логина
            existing_user = execute_query(
                "SELECT id FROM users WHERE username = %s AND id != %s",
                (user_data.login, user_id),
                fetch=True,
            )
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Логин уже используется",
                )
            update_fields.append(f"username = ${param_index}")
            params.append(user_data.login)
            param_index += 1

        if user_data.password is not None:
            hashed_password = UserService.get_password_hash(user_data.password)
            update_fields.append(f"password_hash = ${param_index}")
            params.append(hashed_password)
            param_index += 1

        if not update_fields:
            # нет полей для обновления -> возвращаем текущего пользователя
            return await UserService.get_user(user_id)

        params.append(user_id)  # ID пользователя в конец

        try:
            placeholders = ", ".join([f"${i+1}" for i in range(len(params))])
            query = f"""
                UPDATE users
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ${param_index}
                RETURNING id, email, username, created_at, updated_at
            """

            result = execute_query(query, tuple(params), fetch=True)

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Пользователь не найден",
                )

            user = result[0]
            return {
                "id": user[0],
                "email": user[1],
                "login": user[2],
                "created_at": user[3].isoformat()
                if user[3]
                else datetime.now().isoformat(),
                "updated_at": user[4].isoformat()
                if user[4]
                else datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Ошибка обновления пользователя: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка обновления пользователя",
            )

    @staticmethod
    async def delete_user(user_id: int):
        # существует ли пользователь
        await UserService.get_user(user_id)

        try:
            # удаляем связанные посты
            execute_query(
                """
                DELETE FROM posts WHERE user_id = %s
            """,
                (user_id,),
            )

            # удаляем самого пользователя
            execute_query(
                """
                DELETE FROM users WHERE id = %s
            """,
                (user_id,),
            )

            return {"message": f"Пользователь с ID {user_id} удален"}
        except Exception as e:
            print(f"Ошибка удаления пользователя: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка удаления пользователя",
            )

    @staticmethod
    async def authenticate_user(email: str, password: str):
        try:
            user = execute_query(
                """
                SELECT id, email, username, password_hash
                FROM users
                WHERE email = %s
            """,
                (email,),
                fetch=True,
            )

            if not user:
                return None

            user = user[0]
            user_id, email, username, password_hash = user

            if not UserService.verify_password(password, password_hash):
                return None

            return {"id": user_id, "email": email, "login": username}
        except Exception as e:
            print(f"Ошибка аутентификации: {e}")
            return None
