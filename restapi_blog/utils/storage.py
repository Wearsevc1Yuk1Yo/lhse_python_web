import json
import os
from datetime import datetime

from core.database import (execute_query, get_db_connection,
                           release_db_connection)
from models.post import Post, next_post_id, posts_db
from models.user import User, next_user_id, users_db

DATA_FILE = "blog_data.json"


def migrate_from_json():
    """данные из blog_data.json в PostgreSQL при первом запуске"""
    if not os.path.exists(DATA_FILE):
        print("Файл данных не найден, пропускаем миграцию")
        return

    print("🔄 Начинаем миграцию данных из JSON в PostgreSQL...")

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Миграция пользователей
        for user_id_str, user_data in data.get("users", {}).items():
            try:
                execute_query(
                    """
                    INSERT INTO users (id, email, username, password_hash, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """,
                    (
                        int(user_id_str),
                        user_data.get("email", ""),
                        user_data.get("login", ""),
                        user_data.get(
                            "password", ""
                        ),  # В реальном проекте здесь должен быть хеш пароля
                        datetime.fromisoformat(user_data.get("created_at"))
                        if user_data.get("created_at")
                        else datetime.now(),
                        datetime.fromisoformat(user_data.get("updated_at"))
                        if user_data.get("updated_at")
                        else datetime.now(),
                    ),
                )
            except Exception as e:
                print(f"Ошибка миграции пользователя {user_id_str}: {e}")

        # Миграция постов
        for post_id_str, post_data in data.get("posts", {}).items():
            try:
                execute_query(
                    """
                    INSERT INTO posts (id, user_id, title, content, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """,
                    (
                        int(post_id_str),
                        post_data.get("author_id") or post_data.get("authorId", 1),
                        post_data.get("title", ""),
                        post_data.get("content", ""),
                        datetime.fromisoformat(post_data.get("created_at"))
                        if post_data.get("created_at")
                        else datetime.now(),
                        datetime.fromisoformat(post_data.get("updated_at"))
                        if post_data.get("updated_at")
                        else datetime.now(),
                    ),
                )
            except Exception as e:
                print(f"Ошибка миграции поста {post_id_str}: {e}")

        print("✅ Миграция данных завершена")

        # Переименовываем старый файл, чтобы не запускать миграцию повторно
        os.rename(DATA_FILE, DATA_FILE + ".backup")
        print(f"📁 Файл {DATA_FILE} переименован в {DATA_FILE}.backup")

    except Exception as e:
        print(f"❌ Ошибка миграции данных: {e}")


def load_data_from_db():
    """Загружает данные из PostgreSQL в память при запуске приложения"""
    global users_db, posts_db, next_user_id, next_post_id

    users_db.clear()
    posts_db.clear()

    try:
        users = execute_query(
            """
            SELECT id, email, username, password_hash, created_at, updated_at
            FROM users
            ORDER BY id
        """,
            fetch=True,
        )

        for user_row in users:
            user_id, email, username, password_hash, created_at, updated_at = user_row
            user = User(email, username, password_hash)
            user.id = user_id
            user.created_at = created_at
            user.updated_at = updated_at
            users_db[user_id] = user

        # Загружаем посты
        posts = execute_query(
            """
            SELECT id, user_id, title, content, created_at, updated_at
            FROM posts
            ORDER BY id
        """,
            fetch=True,
        )

        for post_row in posts:
            post_id, user_id, title, content, created_at, updated_at = post_row
            post = Post(user_id, title, content)
            post.id = post_id
            post.created_at = created_at
            post.updated_at = updated_at
            posts_db[post_id] = post

        # Обновляем счетчики ID
        if users_db:
            next_user_id = max(users_db.keys()) + 1
        if posts_db:
            next_post_id = max(posts_db.keys()) + 1

        print(
            f"✅ Данные загружены из БД: {len(users_db)} пользователей, {len(posts_db)} постов"
        )

    except Exception as e:
        print(f"❌ Ошибка загрузки данных из БД: {e}")
        print("⚠️  Используем данные из памяти (если есть)")


# def save_data():
#
#     print("Кстати сохранение в JSON больше не требуется, данные хранятся в PostgreSQL")


def load_data():
    """
    Основная функция загрузки данных при запуске приложения.
    Сначала пытается загрузить данные из БД, если их нет - из JSON.
    """
    try:
        # проверяем, есть ли данные в БД
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM posts")
        posts_count = cursor.fetchone()[0]
        release_db_connection(conn)

        if users_count > 0 or posts_count > 0:
            print("✅ Найдены данные в базе данных, загружаем из PostgreSQL")
            load_data_from_db()
        else:
            print("🔄 Данных в базе не найдено, проверяем JSON файл")
            if os.path.exists(DATA_FILE):
                # Сначала мигрируем из JSON
                migrate_from_json()
                # Затем загружаем из БД
                load_data_from_db()
            else:
                print(
                    "ℹ️  Ни данных в БД, ни JSON файла не найдено. Запускаем с чистого состояния"
                )

    except Exception as e:
        print(f"⚠️  Ошибка при работе с базой данных: {e}")
        print("🔄 Пытаемся загрузить данные из JSON файла")

        if os.path.exists(DATA_FILE):
            try:
                # старый JSON файл
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # воосстанова данных в памяти
                for user_id_str, user_data in data.get("users", {}).items():
                    try:
                        user_id = int(user_id_str)
                        user = User(
                            email=user_data.get("email", ""),
                            login=user_data.get("login", ""),
                            password=user_data.get("password", ""),
                        )
                        user.id = user_id
                        created_at_str = user_data.get("created_at") or user_data.get(
                            "createdAt", ""
                        )
                        updated_at_str = user_data.get("updated_at") or user_data.get(
                            "updatedAt", ""
                        )
                        if created_at_str:
                            user.created_at = datetime.fromisoformat(created_at_str)
                        if updated_at_str:
                            user.updated_at = datetime.fromisoformat(updated_at_str)
                        users_db[user_id] = user
                    except Exception as e:
                        print(f"❌ Ошибка загрузки пользователя {user_id_str}: {e}")

                for post_id_str, post_data in data.get("posts", {}).items():
                    try:
                        post_id = int(post_id_str)
                        post = Post(
                            author_id=post_data.get("author_id")
                            or post_data.get("authorId", 1),
                            title=post_data.get("title", ""),
                            content=post_data.get("content", ""),
                        )
                        post.id = post_id
                        created_at_str = post_data.get("created_at") or post_data.get(
                            "createdAt", ""
                        )
                        updated_at_str = post_data.get("updated_at") or post_data.get(
                            "updatedAt", ""
                        )
                        if created_at_str:
                            post.created_at = datetime.fromisoformat(created_at_str)
                        if updated_at_str:
                            post.updated_at = datetime.fromisoformat(updated_at_str)
                        posts_db[post_id] = post
                    except Exception as e:
                        print(f"❌ Ошибка загрузки поста {post_id_str}: {e}")

                next_user_id = data.get("next_user_id", 1)
                next_post_id = data.get("next_post_id", 1)
                print(
                    f"✅ Данные загружены из JSON файла: {len(users_db)} пользователей, {len(posts_db)} постов"
                )

                print("🔄 Мигрируем загруженные данные в PostgreSQL...")
                migrate_from_json()
                load_data_from_db()

            except Exception as e:
                print(f"❌ Ошибка загрузки из JSON: {e}")
        else:
            print(
                "ℹ️  Не удалось подключиться к БД и JSON файл не найден. Запускаем с чистого состояния"
            )


def get_data_stats():
    """Возвращает статистику по данным из базы данных"""
    try:
        users_count = execute_query("SELECT COUNT(*) FROM users", fetch=True)[0][0]
        posts_count = execute_query("SELECT COUNT(*) FROM posts", fetch=True)[0][0]

        return {
            "users_count": users_count,
            "posts_count": posts_count,
            "using_database": True,
            "data_source": "PostgreSQL",
        }
    except Exception as e:
        print(f"Ошибка получения статистики: {e}")

        return {
            "users_count": len(users_db),
            "posts_count": len(posts_db),
            "using_database": False,
            "data_source": "Memory",
            "error": str(e),
        }
