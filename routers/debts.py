from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from db import SessionLocal
from auth.auth import login, guard_role, TokenPayload
from sqlalchemy.orm import Session, joinedload
from models import Debts, Transactions
from schemas import DebtsResponse, DebtsCreate, DebtsUpdate
from sqlalchemy import func
import logging
# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём роутер для пользователей
router = APIRouter(
    prefix="/debts",
    tags=["debts"],  # Группировка в Swagger UI
)

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

  
@router.get("/",
            summary="Получить долги",
            response_model=List[DebtsResponse])
def get_debts(
        current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
        
        db: Session = Depends(get_db)
        ):
    try:
        logger.info(f"Получение долгов для user_id: {current_user.user_id}")
        
        # Загружаем долги с подсчётом суммы транзакций
        debts = db.query(
            Debts,
            func.coalesce(func.sum(Transactions.sum), 0).label("transactions_sum")
        ).join(
            Transactions, 
            Transactions.debt_id == Debts.id,
            isouter=True
        ).options(
            joinedload(Debts.transactions)
        ).group_by(Debts.id)
        
        if current_user.role != "admin":
            debts = debts.filter(Debts.user_id == current_user.user_id)
        
        debts = debts.all()
        
        if not debts:
            raise HTTPException(status_code=404, detail="Долги не найдены")
        
        # Преобразуем результат в нужный формат
        result = []
        for debt, transactions_sum in debts:
            debt_dict = debt.__dict__
            debt_dict["transactions_sum"] = transactions_sum
            result.append(debt_dict)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении долгов: {str(e)}"
        )

       
@router.post("/",
            summary="Создать новый долг",
            response_model=DebtsResponse,
            status_code=status.HTTP_201_CREATED)
def create_debt(
        debt_data: DebtsCreate,
        current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
        db: Session = Depends(get_db)
        ):
    try:
        logger.info(f"Создание долга для user_id: {current_user.user_id}")
        
        # Создаем новый долг
        new_debt = Debts(
            name=debt_data.name,
            who_gave=debt_data.who_gave,
            date_take=debt_data.date_take,
            date_end=debt_data.date_end,
            comments=debt_data.comments,
            balance=debt_data.balance,
            svg=debt_data.svg,
            user_id=current_user.user_id
        )
        
        db.add(new_debt)
        db.commit()
        db.refresh(new_debt)
        
        return new_debt
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании долга: {str(e)}"
        )

@router.put("/{debt_id}",
           summary="Обновить информацию о долге",
           response_model=DebtsResponse)
def update_debt(
        debt_id: int,
        debt_data: DebtsUpdate,
        current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
        db: Session = Depends(get_db)
        ):
    try:
        logger.info(f"Обновление долга {debt_id} для user_id: {current_user.user_id}")
        
        # Получаем долг из базы данных
        debt = db.query(Debts).filter(Debts.id == debt_id).first()
        
        if not debt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Долг не найден"
            )
        
        # Проверяем, принадлежит ли долг текущему пользователю
        if debt.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для редактирования этого долга"
            )
        
        # Обновляем поля
        if debt_data.name is not None:
            debt.name = debt_data.name
        if debt_data.who_gave is not None:
            debt.who_gave = debt_data.who_gave
        if debt_data.date_take is not None:
            debt.date_take = debt_data.date_take
        if debt_data.date_end is not None:
            debt.date_end = debt_data.date_end
        if debt_data.comments is not None:
            debt.comments = debt_data.comments
        if debt_data.balance is not None:
            debt.balance = debt_data.balance
        if debt_data.svg is not None:
            debt.svg = debt_data.svg
        
        debt.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(debt)
        
        return debt
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении долга: {str(e)}"
        )
        
@router.delete("/{debt_id}",
              summary="Удалить долг",
              status_code=status.HTTP_204_NO_CONTENT)
def delete_debt(
        debt_id: int,
        current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
        db: Session = Depends(get_db)
        ):
    try:
        logger.info(f"Удаление долга {debt_id} для user_id: {current_user.user_id}")
        
        # Получаем долг из базы данных
        debt = db.query(Debts).filter(Debts.id == debt_id).first()
        
        if not debt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Долг не найден"
            )
        
        # Проверяем, принадлежит ли долг текущему пользователю (если не админ)
        if debt.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для удаления этого долга"
            )
        
        db.delete(debt)
        db.commit()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении долга: {str(e)}"
        )