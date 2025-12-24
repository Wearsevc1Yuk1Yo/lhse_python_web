import atexit
import urllib.parse
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from core.config import settings

connection_pool = None

def fix_url_encoding(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.username and parsed.password:
            username = urllib.parse.unquote(parsed.username)
            password = urllib.parse.unquote(parsed.password)
            netloc = f"{username}:{password}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            fixed_url = urllib.parse.urlunparse((
                parsed.scheme, netloc, parsed.path, 
                parsed.params, parsed.query, parsed.fragment
            ))
            return fixed_url
        return url
    except Exception as e:
        print(f"Предупреждение при обработке URL: {e}")
        return url
    

fixed_database_url = fix_url_encoding(settings.DATABASE_URL)
print(fixed_database_url)

def init_connection_pool():

    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = SimpleConnectionPool(
                1, 10, 
                dsn=fixed_database_url,
                client_encoding="KOI8R"
            )
            print("✅ Connection pool инициализирован")
        except Exception as e:
            print(f"❌ Ошибка создания connection pool: {e}")
            connection_pool = None
    return connection_pool

def close_connection_pool():
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        print("✅ Все соединения с базой данных закрыты")
        connection_pool = None

atexit.register(close_connection_pool)

def get_db_connection():
    global connection_pool
    pool = init_connection_pool()
    if not pool:
        raise Exception("База данных недоступна")
    return pool.getconn()

def release_db_connection(conn):
    global connection_pool
    if connection_pool:
        connection_pool.putconn(conn)

def execute_query(query, params=None, fetch=False):
    conn = get_db_connection()
    conn.set_client_encoding('KOI8R')
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
