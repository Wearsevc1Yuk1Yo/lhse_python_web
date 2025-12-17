from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


async def not_found_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"detail": "Ресурс не найден"})
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "title": "404 - Страница не найдена",
            "message": "Запрошенная страница не существует.",
        },
        status_code=404,
    )


async def bad_request_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=400, content={"detail": exc.detail})
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "title": "400 - Ошибка валидации",
            "message": exc.detail or "Неверные данные.",
        },
        status_code=400,
    )


async def internal_error_handler(request: Request, exc: Exception):
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500, content={"detail": "Внутренняя ошибка сервера"}
        )
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "title": "500 - Ошибка сервера",
            "message": "Что-то пошло не так.",
        },
        status_code=500,
    )
