# from fastapi import FastAPI
# import db
# from db import Base, engine
# from models import User, Transactions
# from routers import users, transactions, categories
# from auth import auth
# from fastapi.openapi.utils import get_openapi
# from fastapi.middleware.cors import CORSMiddleware

# # Создание таблиц в базе данных
# Base.metadata.create_all(bind=engine)
# print("✅ Таблицы созданы!")


# # Настроим FastAPI с функцией для создания OpenAPI схемы
# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
#     openapi_schema = get_openapi(
#         title=app.title,
#         version=app.version,
#         description=app.description,
#         routes=app.routes,
#     )
#     openapi_schema["components"]["securitySchemes"] = {
#         "BearerAuth": {
#             "type": "http",
#             "scheme": "bearer",
#             "bearerFormat": "JWT"
#         }
#     }
#     for path in openapi_schema["paths"].values():
#         for method in path.values():
#             method.setdefault("security", [{"BearerAuth": []}])
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema

# app = FastAPI(
#     title="Easy Plan API",
#     description="API для Easy Plan",
#     version="0.1.0",
#     docs_url="/api/docs",
#     redoc_url="/api/redoc",
#     openapi_url="/api/openapi.json",
#     openapi_tags=[
#         {"name": "auth", "description": "Авторизация"},
#         {"name": "users", "description": "Операции с пользователями"},
#         {"name": "transactions", "description": "Операции с транзакциями"},
#         {"name": "categories", "description": "Операции с категориями"},
#     ]
# )


# # Подключение функции custom_openapi к app
# app.openapi = custom_openapi
# # Настройка CORS (если нужно)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # Подключаем роутеры после инициализации
# app.include_router(auth.router, prefix="/api")
# app.include_router(users.router, prefix="/api")
# app.include_router(categories.router, prefix="/api")
# app.include_router(transactions.router, prefix="/api")

# print("🚀 Приложение запущено")

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
from fastapi.openapi.utils import get_openapi

app = FastAPI()

# Конфигурация JWT
SECRET_KEY = "mysecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security схема
bearer_scheme = HTTPBearer(auto_error=False)  # не кидает ошибку сам по себе

# Генерация JWT токена
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Получение текущего пользователя из токена
def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Публичный маршрут — получаем токен
@app.get("/token")
def login_for_token():
    token = create_access_token({"sub": "testuser"})
    return {"access_token": token, "token_type": "bearer"}

# Защищённый маршрут
@app.get("/protected")
def read_protected(current_user=Depends(get_current_user)):
    return {"message": f"Hello {current_user['username']}"}

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

app.openapi = custom_openapi
