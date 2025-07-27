
from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from db import SessionLocal


# Goals
# Limits
# Debts


import logging
# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Создаём роутер для пользователей
router = APIRouter(
    prefix="/rules",
    tags=["rules"],  # Группировка в Swagger UI
)

@router.get("/",
            summary="Получить правила"
            )
def get_rules():
    return []