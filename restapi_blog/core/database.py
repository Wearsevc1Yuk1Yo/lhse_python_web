import atexit

import psycopg2
from core.config import settings
from psycopg2 import pool

# пул соединений
connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 10, settings.DATABASE_URL  # мин колво соединений  # макс волво соединений
)


def close_connection_pool():
    """Закрывает все соединения в пуле при завершении работы"""
    if connection_pool:
        connection_pool.closeall()
        print("Все соединения с базой данных закрыты")


# Регистрируем функцию для закрытия соединений при выходе
atexit.register(close_connection_pool)


def get_db_connection():
    """соединение с базой данных из пула"""
    return connection_pool.getconn()


def release_db_connection(conn):
    """соединение обратно в пул"""
    connection_pool.putconn(conn)


def execute_query(query, params=None, fetch=False):
    """функция для выполнения запросов к базе данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = None

        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        release_db_connection(conn)
