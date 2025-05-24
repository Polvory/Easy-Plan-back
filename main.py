from fastapi import FastAPI
import db
from db import Base, engine
from models import User, Transactions
from routers import users, transactions, categories,accounts, rules, accounts_under, debts, limits, targets
from routers.limits import reset_limits_logic  # импортируем функцию сброса
from auth import auth
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from db import SessionLocal
# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)
print("✅ Таблицы созданы!")

def scheduled_reset_limits():
    db = SessionLocal()
    try:
        result = reset_limits_logic(db)
        if result:
            print("Сброс лимитов выполнен планировщиком!")
        else:
            print("Лимиты не найдены для сброса.")
    except Exception as e:
        print(f"Ошибка сброса лимитов в планировщике: {e}")
    finally:
        db.close()

scheduler = BackgroundScheduler()

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
        {"name": "accounts", "description": "Операции с аккаунтами"},
        {"name": "accounts_under", "description": "Операции с подсчетами"},
        {"name": "debts", "description": "Операции с Долгами"},
        {"name": "limits", "description": "Операции с Лимитами"},
        {"name": "targets", "description": "Операции с Целями"},
        
        
        
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
app.include_router(accounts.router, prefix="/api")
# app.include_router(rules.router, prefix="/api")
# app.include_router(accounts_under.router, prefix="/api")
app.include_router(debts.router, prefix="/api")
app.include_router(limits.router, prefix="/api")
app.include_router(targets.router, prefix="/api")



# Запуск планировщика при старте приложения
@app.on_event("startup")
def start_scheduler():
    # Добавляем задачу, которая выполняется раз в минуту
    scheduler.add_job(scheduled_reset_limits, CronTrigger.from_crontab("* * * * *"))
    scheduler.start()
    print("🚀 Приложение запущено")

# Остановка планировщика при завершении приложения (опционально)
@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
    print("Scheduler stopped!")




