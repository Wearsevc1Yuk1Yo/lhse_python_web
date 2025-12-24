import atexit
import urllib.parse

import psycopg2
from core.config import settings
from psycopg2.pool import SimpleConnectionPool


def fix_url_encoding(url: str) -> str:
    """Исправляет проблему с кодировкой в URL базы данных"""
    try:
        parsed = urllib.parse.urlparse(url)

        # Если есть username/password, декодируем их
        if parsed.username and parsed.password:
            username = urllib.parse.unquote(parsed.username)
            password = urllib.parse.unquote(parsed.password)

            # Формируем новый netloc
            netloc = f"{username}:{password}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"

            # Собираем URL заново
            fixed_url = urllib.parse.urlunparse(
                (
                    parsed.scheme,
                    netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )
            return fixed_url
        return url
    except Exception as e:
        print(f"Предупреждение при обработке URL: {e}")
        return url


# Исправляем строку подключения
fixed_database_url = fix_url_encoding(settings.DATABASE_URL)

print(fixed_database_url)
print(settings.DATABASE_URL)

# Создаем пул соединений с явным указанием кодировки
connection_pool = SimpleConnectionPool(
    1,  # Минимальное количество соединений
    10,  # Максимальное количество соединений
    dsn=fixed_database_url,
    client_encoding="KOI8R",
)


def close_connection_pool():
    """Закрывает все соединения в пуле при завершении работы"""
    if connection_pool:
        connection_pool.closeall()
        print("Все соединения с базой данных закрыты")


# Регистрируем функцию для закрытия соединений при выходе
atexit.register(close_connection_pool)


def get_db_connection():
    """Возвращает соединение с базой данных из пула"""
    return connection_pool.getconn()


def release_db_connection(conn):
    """Возвращает соединение обратно в пул"""
    connection_pool.putconn(conn)


def execute_query(query, params=None, fetch=False):
    """
    функция для выполнения запросов к базе данных"""

    conn = get_db_connection()
    conn.set_client_encoding("KOI8R")

    cursor = conn.cursor()

    try:
        cursor.execute(query, params or ())
        conn.commit()
        if fetch:
            return cursor.fetchall()
        return True

    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка SQL: {query}")
        print(f"   Параметры: {params}")
        print(f"   Ошибка: {e}")
        raise

    finally:
        cursor.close()
        release_db_connection(conn)
