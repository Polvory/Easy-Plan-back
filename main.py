from fastapi import FastAPI
import db  # подключение произойдёт автоматически
from db import Base, engine  # Импорт движка и базового класса
from models import User, Transactions      # Импортируй модель, чтобы SQLAlchemy "увидел" её
from routers import users
from routers import transactions
from routers import categories


# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)
print("✅ Таблицы созданы!")
print("🚀 Приложение запущено")

app = FastAPI(
    title="Easy Plan API",
    description="API для Easy Plan",
    version="0.1.0",
    docs_url="/api/docs",  # Префикс для Swagger UI
    openapi_tags=[{
        "name": "users",
        "description": "Операции с пользователями",
    },
    {
        "name": "transactions",
        "description": "Операции с транзакциями",
    },
     {
        "name": "categories",
        "description": "Операции с категориями",
    },

    ]
)

# Подключаем роутер пользователей
app.include_router(users.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")  # Добавляем роутер для транзакций

@app.get("/")
def read_root():
    return {"message": "Привет, мир!"}


