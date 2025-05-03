from fastapi import FastAPI
import db
from db import Base, engine
from models import User, Transactions
from routers import users, transactions, categories
from auth import auth
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)
print("✅ Таблицы созданы!")

# Swagger: добавить поддержку авторизации
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="JWT Swagger Auth Example",
        version="1.0",
        description="Testing JWT bearer in Swagger",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = FastAPI(
    title="Easy Plan API",
    description="API для Easy Plan",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    openapi_tags=[
        {"name": "auth", "description": "Авторизация"},
        {"name": "users", "description": "Операции с пользователями"},
        {"name": "transactions", "description": "Операции с транзакциями"},
        {"name": "categories", "description": "Операции с категориями"},
    ]
)


# Подключение функции custom_openapi к app
app.openapi = custom_openapi
# Настройка CORS (если нужно)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключаем роутеры после инициализации
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")

print("🚀 Приложение запущено")


