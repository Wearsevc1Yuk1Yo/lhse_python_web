import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def hello():
    return {"message": "✅ Сервер работает!"}


if __name__ == "__main__":
    print("Откройте в браузере: http://127.0.0.1:8000/")
    uvicorn.run(app, host="0.0.0.0", port=8000)
