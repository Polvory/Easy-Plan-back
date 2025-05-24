from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from db import SessionLocal
from models import Limits, User  # Добавляем импорт модели Transaction
from sqlalchemy.orm import Session
from datetime import datetime
from auth.auth import login, guard_role, TokenPayload
from dateutil.relativedelta import relativedelta
import logging

from schemas import CreateLimit, LimitOut, LimitUpdate
# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём роутер для пользователей
router = APIRouter(
    prefix="/limits",
    tags=["limits"],  # Группировка в Swagger UI
)


# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.get("/", 
            summary="Получить лимиты", 
            response_model=List[LimitOut],
            status_code=status.HTTP_200_OK            
            )
def get_limits(
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db),
):
    limits = db.query(Limits)
    logger.info(f"Получение лимитов для user_id: {current_user.user_id}")
    if limits is not None:
        limits = limits.filter(Limits.user_id == current_user.user_id)
    else:
         raise HTTPException(status_code=404, detail="No limits found")
    return limits  


@router.post("/create", summary="Создать лимит", status_code=status.HTTP_201_CREATED)
def create_limits(
    limit: CreateLimit,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Добавление категории для user_id: {current_user.user_id}")
        # 🔍 Проверка на существование лимита с такой категорией у пользователя
        existing_limit = db.query(Limits).filter_by(
            user_id=current_user.user_id,
            category_id=limit.category_id
        ).first()

        if existing_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Лимит с такой категорией уже существует у пользователя"
            )
        new_limit = Limits(
            balance=limit.balance,
            date_update=limit.date_update,
            user_id=current_user.user_id,
            category_id=limit.category_id,
        )
        db.add(new_limit)
        db.commit()
        db.refresh(new_limit)
        return new_limit
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании лимита: {str(e)}"
        )
        


@router.delete("/", 
               summary="Удалить лимит",
               status_code=status.HTTP_204_NO_CONTENT)
def delete_limits(
    limit_id: int,
    db: Session = Depends(get_db)
):
    try:
        user_id = 1
        logger.info(f"Удаление лимита {limit_id} для user_id: {user_id}")

        # Получаем долг из базы данных
        limit = db.query(Limits).filter(Limits.id == limit_id).first()
        
        if not limit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Лимит не найден"
            )
        
        # Проверяем, принадлежит ли долг текущему пользователю (если не админ)
        if limit.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для удаления этого долга"
            )
        
        db.delete(limit)
        db.commit()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении долга: {str(e)}"
        )

def reset_limits_logic(db: Session):
    today = datetime.utcnow().date()
    limits = db.query(Limits).all()
    if not limits:
        return False

    for limit in limits:
        date_update_obj = datetime.strptime(limit.date_update, "%Y-%m-%d").date()
        if date_update_obj == today:
            limit.current_spent = 0
            limit.updated_at = datetime.utcnow()
            new_date = date_update_obj + relativedelta(months=1)
            limit.date_update = new_date.isoformat()

    db.commit()
    return True


@router.put("/reset_all_limits", summary="Сбросить лимиты")
def reset_all_limits(db: Session = Depends(get_db)):
    try:
        result = reset_limits_logic(db)
        if not result:
            raise HTTPException(status_code=404, detail="Лимиты не найдены")
        return {"message": "Лимиты сброшены (по дате обновления)"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при сбросе лимитов: {str(e)}")


@router.put("/", summary="Редактировать лимит", 
            response_model=LimitOut,
            status_code=status.HTTP_200_OK 
            )
def edite_limits(
    limit_id: int,
    update_data:LimitUpdate,
    db: Session = Depends(get_db)):
    try:
        user_id = 1
        logger.info(f"Обновляем счет для user_id: {user_id}")
         # Получаем долг из базы данных
        limit = db.query(Limits).filter(Limits.id == limit_id).first()
        
        if not limit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Лимит не найден"
            )
        # Проверяем, принадлежит ли долг текущему пользователю
        if limit.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для редактирования этого лимита"
            )  

        # Обновляем поля
        if update_data.balance is not None:
            limit.balance = update_data.balance
        if update_data.date_update is not None:
            limit.date_update = update_data.date_update
        limit.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(limit)    
        return limit
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении лимита: {str(e)}"
        )
