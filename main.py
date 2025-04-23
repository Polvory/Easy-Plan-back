from fastapi import FastAPI
import db  # подключение произойдёт автоматически
from db import Base, engine  # Импорт движка и базового класса
from models import User      # Импортируй модель, чтобы SQLAlchemy "увидел" её



# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)
print("✅ Таблицы созданы!")

print("🚀 Приложение запущено")
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Привет, мир!"}

@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Привет, {name}!"}
