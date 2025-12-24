# import os
from typing import Optional

# import psycopg2
import uvicorn
from core.config import settings
from core.database import execute_query
from core.exceptions import (bad_request_handler, internal_error_handler,
                             not_found_handler, templates)
from fastapi import FastAPI, Form, Request, status
# from fastapi import Response, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
# from models.post import posts_db
# from models.user import users_db
from routers import posts_router, users_router
from routers.auth import router as auth_router
from schemas.comment import CommentCreate
from schemas.post import PostCreate, PostUpdate
from schemas.user import UserCreate
from services.comment_service import CommentService
from services.post_service import PostService
from services.user_service import UserService
from utils.storage import load_data

app = FastAPI(title="Simple Blog API")

# middleware для сессий (до всех других middleware и роутеров)
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(users_router)
app.include_router(posts_router)
app.include_router(auth_router)

app.add_exception_handler(404, not_found_handler)
app.add_exception_handler(400, bad_request_handler)
app.add_exception_handler(500, internal_error_handler)


@app.get("/debug-db")
async def debug_db():
    """Отладка БД — покажет всех пользователей"""
    result = execute_query(
        "SELECT id, email, username FROM users ORDER BY id;", fetch=True
    )
    return {"users": result}


def test_connection():
    from core.database import connection_pool

    try:
        conn = connection_pool.getconn()
        print("✅ Успешное подключение к базе данных PostgreSQL")
        connection_pool.putconn(conn)
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        print(f"⚠️  Проверьте строку подключения: {settings.DATABASE_URL}")
        return False
    return True


def test_database_connection():
    """Проверяет подключение к базе данных PostgreSQL"""
    try:
        # Попытка подключения к базе данных
        from core.database import connection_pool

        conn = connection_pool.getconn()
        print("✅ Успешное подключение к базе данных PostgreSQL")
        connection_pool.putconn(conn)
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        print(f"⚠️  Приложение будет работать с JSON-файлом вместо PostgreSQL")
        print(f"Проверьте строку подключения: {settings.DATABASE_URL}")
        return False


# Load data on startup
load_data()

# Проверяем подключение к базе данных при запуске
if __name__ == "__main__":
    print(
        f"🚀 Запуск приложения '{settings.PROJECT_NAME}' "
        f"версии {settings.PROJECT_VERSION}"
    )
    print(f"📁 Путь к файлу данных: {settings.DATA_FILE}")

    # Проверяем подключение к базе данных
    db_connected = test_database_connection()

    # Показываем статистику данных
    from utils.storage import get_data_stats

    stats = get_data_stats()

    print(
        f"📊 Статистика данных: {stats['users_count']} пользователей, "
        f"{stats['posts_count']} постов"
    )


# Helper function to get current user
def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    print(f"🔍 get_current_user: session user_id={user_id}")

    if not user_id:
        return None

    result = execute_query(
        """
        SELECT id, email, username, created_at, updated_at
        FROM users
        WHERE id = %s
        """,
        (user_id,),
        fetch=True,
    )
    print(f"👤 DB result: {result}")

    if not result:
        return None

    row = result[0]
    user = {
        "id": row[0],
        "email": row[1],
        "login": row[2],
        "created_at": row[3],
        "updated_at": row[4],
    }

    print(f"✅ Current user: {user['login']} (ID: {user['id']})")
    return user


# Инициализация БД при старте
@app.on_event("startup")
async def init_db():
    try:
        # таблицы
        with open("hw2/database/ddl.sql", "r", encoding="utf-8") as f:
            execute_query(f.read())
        print("✅ Таблицы созданы")

        # тест пользователь
        execute_query(
            """
            INSERT INTO users (email, username, password_hash)
            VALUES ('test@example.com', 'testuser', 'testpass')
            ON CONFLICT DO NOTHING
        """
        )
        print("✅ Тестовый пользователь создан")

    except Exception as e:
        print(f"⚠️ Ошибка инициализации БД: {e}")


# @app.on_event("startup")
# async def init_db():
#     try:
#         # таблицы
#         with open("hw2/database/ddl.sql", "r", encoding="utf-8") as f:
#             ddl_sql = f.read()
#         execute_query(ddl_sql)
#         print("✅ Таблицы созданы")

#         # Тестовые пользователи
#         execute_query("""
#             INSERT INTO users (email, username, password_hash)
#             VALUES ('test@example.com', 'testuser', 'testpass')
#             ON CONFLICT DO NOTHING
#         """)
#         print("✅ Тестовый пользователь: testuser/testpass")

#     except Exception as e:
#         print(f"⚠️ Ошибка инициализации БД: {e}")


# HTML Routes
@app.get("/")
async def home_page(request: Request, q: Optional[str] = None):
    current_user = get_current_user(request)

    posts_list = await PostService.get_all_posts(search_query=q)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "posts": posts_list,
            "current_user": current_user,
        },
    )


@app.get("/post/{post_id}")
async def view_post_page(request: Request, post_id: int):
    current_user = get_current_user(request)

    try:
        post = await PostService.get_post(post_id)
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            return not_found_handler(request, None)
        raise

    return templates.TemplateResponse(
        "view_post.html",
        {"request": request, "post": post, "current_user": current_user},
    )


@app.get("/create-post")
async def create_post_page(request: Request):
    current_user = get_current_user(request)

    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "create_post.html", {"request": request, "current_user": current_user}
    )


@app.post("/create-post")
async def handle_create_post(
    request: Request, title: str = Form(), content: str = Form()
):
    current_user = get_current_user(request)

    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    post_data = PostCreate(author_id=current_user["id"], title=title, content=content)
    await PostService.create_post(post_data, current_user_id=current_user["id"])
    return RedirectResponse(url="/", status_code=303)


@app.get("/edit-post/{post_id}")
async def edit_post_page(request: Request, post_id: int):
    current_user = get_current_user(request)

    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    try:
        post = await PostService.get_post(post_id)
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            return not_found_handler(request, None)
        raise

    if post["author_id"] != current_user["id"]:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Ошибка доступа",
                "message": "Вы можете редактировать только свои посты",
            },
            status_code=403,
        )

    post_data = {"id": post["id"], "title": post["title"], "content": post["content"]}

    return templates.TemplateResponse(
        "edit_post.html",
        {"request": request, "post": post_data, "current_user": current_user},
    )


@app.post("/edit-post/{post_id}")
async def handle_edit_post(
    request: Request, post_id: int, title: str = Form(), content: str = Form()
):
    current_user = get_current_user(request)

    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    # Проверяем, что пользователь является автором поста
    # if post_id in posts_db and posts_db[post_id].author_id != current_user["id"]:
    #     return templates.TemplateResponse(
    #         "error.html",
    #         {
    #             "request": request,
    #             "title": "Ошибка доступа",
    #             "message": "Вы можете редактировать только свои посты",
    #         },
    #         status_code=403,
    #     )
    post_data = PostUpdate(title=title, content=content)
    await PostService.update_post(
        post_id, post_data, current_user_id=current_user["id"]
    )
    return RedirectResponse(url=f"/post/{post_id}", status_code=303)


@app.get("/register")
async def register_page(request: Request):
    current_user = get_current_user(request)
    return templates.TemplateResponse(
        "register.html", {"request": request, "current_user": current_user}
    )


@app.post("/register")
async def handle_register(request: Request):
    form = await request.form()
    email = form.get("email")
    login = form.get("login")
    password = form.get("password")

    try:
        user_data = UserCreate(email=email, login=login, password=password)
        new_user = await UserService.create_user(user_data)

        request.session["user_id"] = new_user["id"]
        print(f"✅ Автологин: user_id={new_user['id']} ({new_user['login']})")

        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    except ValidationError as e:
        print(f"❌ Регистрация ошибка: {e}")
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": str(e)},
            status_code=400,
        )

    # except HTTPException:
    #     raise

    # except Exception as e:
    #     print(f"Регистрация ошибка: {e}")
    #     return templates.TemplateResponse(
    #         "register.html",
    #         {"request": request, "error": "Ошибка сервера"},
    #         status_code=500,
    #     )


@app.get("/login")
async def login_page(request: Request):
    current_user = get_current_user(request)

    if current_user:
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "login.html", {"request": request, "current_user": current_user}
    )


@app.post("/login")
async def handle_login(request: Request):
    form = await request.form()

    print(f"📝 Форма: {dict(form)}")

    login_input = (form.get("login") or "").strip()
    password = form.get("password")

    print(
        f"🔍 Логин: '{login_input}' (длина: {len(login_input or '')}), пароль: {len(password or '')}симв."
    )

    if not login_input:
        print("❌ Пустое поле логина")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Введите логин"},
            status_code=400,
        )

    print(f"Логин попытка: '{login_input}'")

    result = execute_query(
        """
        SELECT id, password_hash, username
        FROM users
        WHERE username = %s OR email = %s
        """,
        (login_input, login_input),
        fetch=True,
    )
    if not result:
        print("❌ Пользователь не найден")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль"},
            status_code=400,
        )

    user_id, password_hash, username = result[0]
    print(f"👤 Найден: {username} (ID: {user_id})")

    if not UserService.verify_password(password, password_hash):
        print("❌ Неверный пароль")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль"},
            status_code=400,
        )
    request.session["user_id"] = user_id
    print(f"✅ Логин успешен: {username}")
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user_id", None)
    return RedirectResponse(url="/", status_code=303)


# @app.get("/switch-user/{user_id}")
# async def switch_user(request: Request, user_id: int):
#     if user_id in users_db:
#         request.session["user_id"] = user_id
#     return RedirectResponse(url="/", status_code=303)


@app.get("/delete-post/{post_id}")
async def delete_post_page(request: Request, post_id: int):
    current_user = get_current_user(request)

    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    # Проверяем, что пользователь является автором поста
    # if post_id in posts_db and posts_db[post_id].author_id != current_user["id"]:
    #     return templates.TemplateResponse(
    #         "error.html",
    #         {
    #             "request": request,
    #             "title": "Ошибка доступа",
    #             "message": "Вы можете удалять только свои посты",
    #         },
    #         status_code=403,
    #     )

    await PostService.delete_post(post_id, current_user_id=current_user["id"])
    return RedirectResponse(url="/", status_code=303)


@app.post("/post/{post_id}/comment")
async def add_comment(
    request: Request,
    post_id: int,
    content: str = Form(...),
    parent_comment_id: int | None = Form(None),
):
    """
    Обработчик формы добавления комментария к посту.
    """
    current_user = get_current_user(request)

    print(
        f"🗣️ Комментарий: user_id={current_user['id'] if current_user else None}, post_id={post_id}"
    )
    print(f"   content='{content[:50]}...'")

    if not current_user:
        print("❌ Нет пользователя")
        return RedirectResponse(url="/login", status_code=303)

    comment_data = CommentCreate(
        post_id=post_id,
        parent_comment_id=parent_comment_id,
        content=content,
    )
    try:
        await CommentService.create_comment(
            comment_data, current_user_id=current_user["id"]
        )
        print("✅ CommentService.create_comment() УСПЕШЕН!")
    except Exception as e:
        print(f"❌ ОШИБКА CommentService: {e}")
        import traceback

        print(traceback.format_exc())

    return RedirectResponse(url=f"/post/{post_id}", status_code=303)


if __name__ == "__main__":
    # middleware для сессий
    from starlette.middleware.sessions import SessionMiddleware

    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    # подключение к базе данных
    print("🔍 Проверка подключения к базе данных...")
    db_connected = test_database_connection()

    if db_connected:
        print("✅ База данных доступна, запускаем приложение")
    else:
        print("⚠️  База данных недоступна, приложение будет работать с JSON-файлом")

    print(
        f"🚀 Запуск приложения '{settings.PROJECT_NAME}'"
        "версии {settings.PROJECT_VERSION}"
    )
    uvicorn.run(app, host="127.0.0.1", port=8000)
