
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
    prefix="/accounts_under",
    tags=["accounts_under"],  # Группировка в Swagger UI
)

@router.get("/",
            summary="Создать подсчет"
            )
def get_rules():
    return []