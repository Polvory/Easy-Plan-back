from datetime import date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from models import Debts, User, Categories, Accounts, Transactions, Limits, Targets  # Добавляем импорт модели Transaction
from db import SessionLocal
from sqlalchemy.orm import Session
from schemas import TransactionResponse, CreateTransaction, TransactionsTypeEnum
from auth.auth import  guard_role, TokenPayload
import logging
# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Создаём роутер для пользователей
router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],  # Группировка в Swagger UI
)

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=TransactionResponse,
    summary="Создать новую транзакцию",
)

async def create_transaction(
    transaction_data: CreateTransaction,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    """
    Это модель транзакции, содержащая следующие поля: 
    
    - sum — сумма операции (например, 1000), обязательное поле. 
    - moded — тип транзакции, строго ограниченный значениями перечисления (income, expense).  
    - repeat_operation — необязательный флаг, указывающий, является ли операция повторяющейся (по умолчанию false). 
    - category_id — необязательный ID категории, к которой относится транзакция. 
    - account_id — обязательный ID счёта, с которым связана операция. 
    - debt_id — полностью необязательное поле для привязки к долгу (может быть null). 
    - target_id — также необязательное поле, указывающее на связанную финансовую цель (может быть null).
    """
    logger.info(f"Создание транзакции для user_id: {current_user.user_id}")
    # Проверяем существование пользователя
    user:User = db.query(User).filter(User.id == current_user.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Указанный пользователь не найден"
        )
    category:Categories = db.query(Categories).filter(Categories.id == transaction_data.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Указанной категория не найдена"
        )
    account:Accounts = db.query(Accounts).filter(Accounts.id == transaction_data.account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Указанной счет не найден"
        )
    if transaction_data.debt_id:
        debt:Debts = db.query(Debts).filter(
            Debts.id == transaction_data.debt_id,
            Debts.user_id == current_user.user_id
        ).first()
        if not debt:
            raise HTTPException(404, "Долг не найден")
    
    if category.moded != transaction_data.moded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Тип транзакции не соответствует типу транзаукции категории"
        )
    
   

    try:
        logger.info(f"Создание транзакции")
        # Сохраняем транзакцию в базе
        # Корректируем баланс счета
        if transaction_data.moded == TransactionsTypeEnum.expense:
            account.balance -= transaction_data.sum
        elif transaction_data.moded == TransactionsTypeEnum.income:
            account.balance += transaction_data.sum
        logger.info(f"Корректируем баланс счета: {account.balance}")  
        
        if transaction_data.debt_id is not None:
            debt = db.query(Debts).filter(Debts.id == transaction_data.debt_id).first()
            if debt:
                if transaction_data.moded == TransactionsTypeEnum.income:
                    # Корректируем баланс долга только для доходных операций
                    if debt.balance > 0:
                        debt.balance = max(0, debt.balance - transaction_data.sum)
                        logger.info(f"Корректируем баланс долга: {debt.balance}")

                        # Если долг погашен полностью
                        if debt.balance <= 0:
                            debt.completed = True
                            logger.info("Долг полностью погашен, отмечаем как завершенный")
                            
        logger.info(f"Корректируем лимит: {category.id}") 
        # ищем лимит где совпадает категория id и юзер id
        limit = db.query(Limits).filter(
            Limits.category_id == category.id,
            Limits.user_id == current_user.user_id
        ).first()
        if limit:
            logger.info(f"Лимит найден: {limit.id}")
            limit.current_spent += transaction_data.sum
            # db.refresh(limit)
            if limit.current_spent > limit.balance:
                logger.info(f"Лимит превышен: {limit.current_spent} > {limit.balance}")
        
         # ищем цель где совпадает цель id и юзер id
        target = db.query(Targets).filter(
            Targets.id == transaction_data.target_id,
            Targets.user_id == current_user.user_id
        ).first()
        if target: 
             logger.info(f"Цель найдена: {target.id}")
             target.balance += transaction_data.sum
             if target.balance >= target.balance_target:
                 target.completed = True
                 logger.info("Цель достигнута, отмечаем как завершенную")
             
         # # Создаем объект транзакции
        new_transaction = Transactions(
            sum=transaction_data.sum,
            moded=transaction_data.moded,
            repeat_operation=transaction_data.repeat_operation,  # Используем Enum значение
            user_id=current_user.user_id,
            category_id=transaction_data.category_id,
            account_id=transaction_data.account_id,
            limit_id=limit.id if limit else None,  # Может быть None
            target_id=target.id if target else None,  # Может быть None
            debt_id=transaction_data.debt_id,  # Может быть None
            currency = account.currency,  # Используем валюту счета
            balance = account.balance
        )  
        
        db.add(new_transaction)
        db.commit()
        # # Обновляем объект чтобы получить сгенерированные поля
        db.refresh(new_transaction)
        # загружаем транзакцию с категорией
        new_transaction.category = category  # присваиваем уже загруженную категорию
        new_transaction.limit = limit  # присваиваем уже загруженный лимит

        return new_transaction
    except Exception as e:
        # В случае ошибки откатываем транзакцию
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании транзакции: {str(e)}"
        )

    

@router.get("/all", 
            response_model=List[TransactionResponse], 
            summary="Получить транзакции с пагинацией")
async def get_all_transactions(
    db: Session = Depends(get_db),
    limit: int = Query(100, gt=0, le=1000, description="Лимит количества записей (1-1000)"),
    date_from: Optional[date] = Query(None, description="Начальная дата фильтрации (в формате YYYY-MM-DD)", example="2025-05-01"),
    date_to: Optional[date] = Query(None, description="Конечная дата фильтрации (в формате YYYY-MM-DD)", example="2025-05-30"),
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    offset: int = Query(0, ge=0, description="Смещение (количество записей для пропуска)"),
    order_by: str = Query("desc", description="Порядок сортировки по дате (asc/desc)"),
    moded: TransactionsTypeEnum = Query(None, description="Тип операции income/expense", example="income"),
    account_id: int = Query(None, description="id счета", example=1),
    limit_id: int = Query(None, description="id лимита", example=2),
    target_id: int = Query(None, description="id цели", example=1)
):
    """
    Получает список транзакций с возможностью фильтрации и пагинации.
    
    Параметры:
    - limit: количество возвращаемых записей (по умолчанию 100)
    - offset: смещение (по умолчанию 0)
    - order_by: порядок сортировки ('asc' или 'desc')
    - date_from: фильтрация по дате (начало периода)
    - date_to: фильтрация по дате (конец периода)
    - moded: тип операции income/expense
    - account_id: id счета
    - limit_id: id лимита
    - target_id: id цели
    """
    logger.info(f"Получает список транзакций user_id: {current_user.user_id}")
    # Проверяем существование пользователя
    user:User = db.query(User).filter(User.id == current_user.user_id).first()
    query = db.query(Transactions)
    if user is not None:
        query = query.filter(Transactions.user_id == user.id)
    else:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Указанный пользователь не найден"
        ) 
         
    if date_from:
        query = query.filter(Transactions.created_at >= date_from)
    if date_to:
        query = query.filter(Transactions.created_at <= date_to)     
    if moded:
        query = query.filter(Transactions.moded == moded)
    if account_id:
        query = query.filter(Transactions.account_id == account_id)
    if limit_id:
        query = query.filter(Transactions.limit_id == limit_id)    
    if target_id:
        query = query.filter(Transactions.target_id == target_id)
    if order_by == "asc":
        query = query.order_by(Transactions.created_at.asc())
    else:
        query = query.order_by(Transactions.created_at.desc())
    
    transactions = query.offset(offset).limit(limit).all()
    return transactions


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить транзакцию и откорректировать баланс",
    description="Удаляет транзакцию и восстанавливает баланс счета, на котором была проведена операция."
)
async def delete_transaction(
    transaction_id: int,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    logger.info(f"Удаление транзакции с ID: {transaction_id} для user_id: {current_user.user_id}")
    
    # Получаем транзакцию из базы
    transaction: Transactions = db.query(Transactions).filter(Transactions.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )
    
    # Проверяем, что транзакция принадлежит текущему пользователю
    if transaction.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на удаление этой транзакции"
        )
    
    # Получаем счет, на котором была проведена операция
    account: Accounts = db.query(Accounts).filter(Accounts.id == transaction.account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Счет не найден"
        )
    
    # Корректируем баланс счета в зависимости от типа транзакции
    if transaction.moded == TransactionsTypeEnum.expense:
        account.balance += transaction.sum  # Если расход, добавляем сумму обратно
    elif transaction.moded == TransactionsTypeEnum.income:
        account.balance -= transaction.sum  # Если доход, вычитаем сумму обратно
    
    # Удаляем транзакцию из базы
    try:
        db.delete(transaction)
        db.commit()
        logger.info(f"Транзакция {transaction_id} удалена и баланс счета откорректирован.")
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении транзакции: {str(e)}"
        )

    return {"detail": "Транзакция успешно удалена и баланс откорректирован"}
# # Перечисление типов транзакций для Pydantic модели
# class TransactionTypeEnum(str, Enum):
#     receipts = 'receipts'
#     expenses = 'expenses'

# # Модель запроса для создания транзакции
# class TransactionCreateRequest(BaseModel):
#     sum: int
#     currency: CurrencyEnum
#     type: TransactionTypeEnum  # Используем Enum для типа
#     user_id: int

#     @validator('sum')
#     def validate_sum(cls, v, values):
#         """
#         Валидация суммы в зависимости от типа транзакции:
#         - Для receipts (поступлений) сумма может быть любой (положительной или отрицательной)
#         - Для expenses (расходов) сумма должна быть положительной
#         """
#         if 'type' in values and values['type'] == TransactionTypeEnum.expenses and v <= 0:
#             raise ValueError('Для расходов сумма должна быть положительной')
#         return v

# # Модель ответа для созданной транзакции
# class TransactionCreateResponse(BaseModel):
#     id: int
#     sum: int
#     currency: str
#     type: str  # Тип транзакции (receipts/expenses)
#     user_id: int
#     created_at: datetime

#     class Config:
#         orm_mode = True

