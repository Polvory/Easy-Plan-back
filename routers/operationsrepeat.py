

# Настройка логгирования
from datetime import datetime, date, timedelta
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from requests import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from auth.auth import TokenPayload, guard_role
from db import SessionLocal
from enums import OperationReapitType
from models import Debts, OperationsRepeat, RepeatOperations, Targets, Transactions, User
from routers.categories import get_category_by_user_id
from routers.debts import get_debts_by_user_id
from routers.limits import get_limit_by_user_id
from routers.tasks import get_task_by_user_id
from routers.transactions import create_transaction
from schemas import CreateOperationsRepeat, CreateRepeatOperation, CreateTransaction, OperationsResponse, OperationsWithLimitsResponse, RepeatOperationListOut, RepeatOperationOut
from fastapi.encoders import jsonable_encoder
import json
from sqlalchemy.orm import Session, joinedload
from dateutil.relativedelta import relativedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём роутер для пользователей
router = APIRouter(
    prefix="/operationsrepeat",
    tags=["operationsrepeat"],  # Группировка в Swagger UI
)

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def loggger_json(data):
    """
    Функция для логирования данных в формате JSON.
    """
    try:
        data_dict = jsonable_encoder(data)
        data_json = json.dumps(data_dict, ensure_ascii=False, indent=2)
        logger.info(f"создаем новую транзакцию на основе текущей операции:\n{data_json}")
    except TypeError as e:
        logger.error(f"Ошибка при преобразовании данных в JSON: {e}")




# Создание операции на повтор
@router.post("/", 
             response_model=List[RepeatOperationOut],
             status_code=status.HTTP_201_CREATED)
def create_repeat_operation(
    operation: CreateRepeatOperation,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db),
):
    """
        Функция для опреаций на повторе, примеры:
        Интервалы: day, week, month, year
        Обезательные поля:
        - "balance": 1000,
        - "date_start": "2025-06-09",  
        - "moded": "expense", "income",  
        - "name": "Зарплата",  
        - "interval": "day",
        - "count": 5
        -  "account_id": 1,
        
        Не обезательные: 
        - "category_id": 0,
        - "debt_id": 0,
        - "target_id": 0,
        - "limit_id": 0,
        - "task_id": 0,    
            
           
            
 
   
    """
    logger.info(operation.date_start)
    user:User = db.query(User).filter(User.id == current_user.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Указанный пользователь не найден"
        )
        
    # Проверка долга
            # Получаем долг из базы данных
    # Проверка долга, если debt_id задан
    if operation.debt_id:
        debt = get_debts_by_user_id(operation.debt_id, current_user.user_id, db)
        if debt is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Долг не найден"
            )
    if operation.category_id:
        category = get_category_by_user_id(operation.category_id, db)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Категория не найдена"
            )
        if category.moded != operation.moded:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Категория не соответствует типу операции"
            )
    if operation.target_id:
        target: Targets = db.query(Targets).filter(Targets.id == operation.target_id, Targets.user_id == current_user.user_id).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Цель не найдена"
            )
    if operation.limit_id:
        limit = get_limit_by_user_id(operation.limit_id, current_user.user_id, db)
        if limit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Лимит не найден"
            )  
            
    if operation.task_id:
        # Проверка задачи, если task_id задан
        task = get_task_by_user_id(operation.task_id, db)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена"
            )  
            
    created_operations = []
    
    current_date = datetime.strptime(operation.date_start, "%Y-%m-%d").date()
    # Начальная дата — сейчас
    # current_date = datetime.utcnow() 
    for i in range(operation.count):
        # Определяем дату следующей операции
        if operation.interval == "day":
            next_date = current_date + timedelta(days=i)
        elif operation.interval == "week":
            next_date = current_date + timedelta(weeks=i)
        elif operation.interval == "month":
            next_date = current_date + relativedelta(months=i)
        elif operation.interval == "year":
            next_date = current_date + relativedelta(years=i)
        else:
            raise HTTPException(status_code=400, detail="Недопустимый интервал повторения")
    
        new_op = RepeatOperations(
            balance=operation.balance,
            moded=operation.moded,
            name =operation.name,
            category_id=operation.category_id if operation.category_id else None,
            account_id=operation.account_id if operation.account_id else None,
            debt_id=operation.debt_id if operation.debt_id else None,
            target_id=operation.target_id if operation.target_id else None,
            limit_id=operation.limit_id if operation.limit_id else None,
            task_id=operation.task_id if operation.task_id else None,
            user_id=current_user.user_id,
            planned_date=next_date  # Предполагается, что есть поле `planned_date` в модели
        )
        
        
        
        db.add(new_op)
        
        created_operations.append(new_op)
        
    
    try:
        loggger_json(created_operations)
        db.commit()
        
        return created_operations
    #     db.add(new_op)
    #     db.commit()
        
    #     return new_op
    except Exception as e:
        db.rollback()
        db.refresh(new_op)
        raise HTTPException(status_code=500, detail=f"Ошибка при создании операции: {str(e)}")

@router.put('/complete', 
            summary="Завершить операцию на повторе",        
            status_code=status.HTTP_200_OK)
async def complete_operation(
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    id: int = Query(None, description="id операции", example=1),
):
    user_id = current_user.user_id
    operation = db.query(RepeatOperations).filter(RepeatOperations.user_id == user_id,
        RepeatOperations.id == id).first()
    
    if operation.completed:
            logger.info(f"Операция {operation.id} уже выполнена.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Операция уже выполнена."
            )
    transaction_data  = CreateTransaction(
                user_id=operation.user_id,
                sum=operation.balance,
                moded=operation.moded,
                repeat_operation=False,  # Указываем, что это повторная операция
                account_id=operation.account_id,
                category_id=operation.category_id if operation.category_id else None,
                debt_id=operation.debt_id if operation.debt_id else None,
                target_id=operation.target_id if operation.target_id else None,
                limit_id=operation.limit_id if operation.limit_id else None,
                task_id=operation.task_id if operation.task_id else None,
                transaction_data = None
                
            )
    loggger_json(transaction_data)
    # Вызываем функцию создания транзакции
    new_transaction = await create_transaction(
            transaction_data=transaction_data,
            current_user=current_user,
            db=db
        )
    logger.info(f"Создана новая транзакция ID: {new_transaction.id}")
    new_transaction_dict = jsonable_encoder(new_transaction)
    new_transaction_json = json.dumps(new_transaction_dict, ensure_ascii=False, indent=2)
    logger.info(f"создаем новую транзакцию на основе текущей операции:\n{new_transaction_json}")           
    operation.completed = True
    operation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(operation)   
    return operation


@router.get("/", 
            summary="Получить операции на повторе",
            response_model=RepeatOperationListOut,        
            status_code=status.HTTP_200_OK)
def get_operations_repeat(
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])), 
    limit: int = Query(100, gt=0, le=1000, description="Лимит количества записей (1-1000)"),
    offset: int = Query(0, ge=0, description="Смещение (количество записей для пропуска)"), 
    date_from: Optional[datetime] = Query(None, description="Начальная дата для фильтрации (planned_date >= date_from)", example="2025-05-01"),
    date_to: Optional[datetime] = Query(None, description="Конечная дата для фильтрации (planned_date <= date_to)", example="2025-12-02"),
    completed: Optional[bool] = Query(None, description="Фильтр по выполненным операциям (True/False)", example=True)
):
    try:
        # Сначала формируем базовый запрос
        query = db.query(RepeatOperations)
        if current_user:
            query = query.filter(RepeatOperations.user_id == current_user.user_id)
        # Фильтрация по датам, если переданы
        if date_from:
            query = query.filter(RepeatOperations.planned_date >= date_from)
        if date_to:
            query = query.filter(RepeatOperations.planned_date <= date_to)
        query = query.filter(RepeatOperations.completed == completed)
        # Сортировка по planned_date по возрастанию
        query = query.order_by(RepeatOperations.planned_date.asc())    
        # Выполняем запрос и получаем результат
        total = query.count()
        reapits = query.offset(offset).limit(limit).all()  
        logger.info(f"Найдено {len(reapits)} операций")
        
        return {
            "total": total,
            'reapits': reapits
        }    
    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при получении данных"
        )
        
  

async def  repeat_operation_logic(db: Session):
      # Получаем текущую дату+время без секунд и микросекунд
    now = datetime.utcnow().replace(second=0, microsecond=0)
    
    # Определяем границы дня (начало и конец)
    start_of_day = now.replace(hour=0, minute=0)
    end_of_day = start_of_day + timedelta(days=1)
    logger.info(start_of_day)
    logger.info(end_of_day)
    # Сначала формируем базовый запрос
   # Формируем запрос для поиска операций с repeat_date = сегодня
    operations = db.query(RepeatOperations).filter(
        RepeatOperations.planned_date >= start_of_day,
        RepeatOperations.planned_date < end_of_day
    ).all()
    
    if not operations:
        logger.info("Нет операций для повторения на сегодня")
        return False
    
    # Логируем найденные операции
    operations_dict = jsonable_encoder(operations)
    operations_json = json.dumps(operations_dict, ensure_ascii=False, indent=2)
    logger.info(f"Найденные операции для повторения:\n{operations_json}")
    
    if operations:
        for operation in operations:
            if operation.completed:
                logger.info(f"Операция {operation.id} уже выполнена, пропускаем.")
                continue
            # Логируем информацию о каждой операции
            logger.info(f"Обработка операции: {operation.id},  дата: {operation.planned_date}")
            operation_dict = jsonable_encoder(operation)
            operation_dict_json = json.dumps(operation_dict, ensure_ascii=False, indent=2)
            logger.info(f"Данные по новой операции:\n{operation_dict_json}")            
           
            current_user = TokenPayload(
                    user_id=operation.user_id,
                    roles=["user"],  # или operation.user.roles если есть такое поле
                    role="user",     # если модель требует отдельное поле role
                    language="ru"    # или другое значение по умолчанию
            )
            logger.info(f"Текущий пользователь: {current_user.user_id}")
            # создаем новую транзакцию на основе текущей операции
            transaction_data  = Transactions(
                user_id=operation.user_id,
                sum=operation.balance,
                moded=operation.moded,
                repeat_operation=False,  # Указываем, что это повторная операция
                account_id=operation.account_id,
                category_id=operation.category_id if operation.category_id else None,
                debt_id=operation.debt_id if operation.debt_id else None,
                target_id=operation.target_id if operation.target_id else None,
                limit_id=operation.limit_id if operation.limit_id else None,
                task_id=operation.task_id if operation.task_id else None,
            )
            loggger_json(transaction_data)
            # Вызываем функцию создания транзакции
            new_transaction = await create_transaction(
                    transaction_data=transaction_data,
                    current_user=current_user,
                    db=db
                )
            logger.info(f"Создана новая транзакция ID: {new_transaction.id}")
    #              # Логируем найденные операции
            new_transaction_dict = jsonable_encoder(new_transaction)
            new_transaction_json = json.dumps(new_transaction_dict, ensure_ascii=False, indent=2)
            logger.info(f"создаем новую транзакцию на основе текущей операции:\n{new_transaction_json}")
            repeat_operation: RepeatOperations = db.query(RepeatOperations).filter(RepeatOperations.id == operation.id).first()
            if not repeat_operation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Операция не найдена"
                )
            repeat_operation.completed = True  # Отмечаем операцию как выполненную 
            repeat_operation.updated_at = datetime.utcnow()  # Обновляем дату обновления   
            # db.delete(repeat_operation)
            db.commit()
    return True


@router.put("/repeat_operation", summary="Повторить операцию (по дате обновления)")
async def repeat_operation(
    db: Session = Depends(get_db)
    ):
    try:
        result = await  repeat_operation_logic(db)
        if not result:
            raise HTTPException(status_code=404, detail="Операции не найдены")
        return {"message": "Операции созданны (по дате обновления)"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при повторе операций: {str(e)}")


@router.delete("/{operation_id}", 
            summary="Удалить операцию на повтор",
            status_code=status.HTTP_204_NO_CONTENT)
def delete_operation_repeat(
    repeat_operation_id: int,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    logger.info(f"Удаление повторяющеся операцию по id с ID: {repeat_operation_id} для user_id: {current_user.user_id}")
    
    repeat_operation: RepeatOperations = db.query(RepeatOperations).filter(RepeatOperations.id == repeat_operation_id).first()
    if not repeat_operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Операция не найдена"
        )
    # Проверяем, что транзакция принадлежит текущему пользователю
    if repeat_operation.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на удаление этой транзакции"
        )
    try:
        db.delete(repeat_operation)
        db.commit()
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении транзакции: {str(e)}"
        )
    return {"detail": "Операция успешно удалена"}
        
# получаем тип операции дату и количество повторений


# создать транзакции на повтор 
# получить id транзакции и создать операцию с данными для транзакции 
# @router.get("/", 
#             summary="Получить операции на повторе",
#             response_model=OperationsWithLimitsResponse,  # Используем новую модель         
#             status_code=status.HTTP_200_OK)
# def get_operations_repeat(
#     db: Session = Depends(get_db),
#     current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
#     limit: int = Query(100, gt=0, le=1000, description="Лимит количества записей (1-1000)"),
#     offset: int = Query(0, ge=0, description="Смещение (количество записей для пропуска)"),
#     order_by: str = Query("desc", description="Порядок сортировки по дате (asc/desc)"),
#     target_id: int = Query(None, description="id цели", example=2),
#     date_from: Optional[date] = Query(None, description="Начальная дата фильтрации (в формате YYYY-MM-DD)", example="2025-05-01"),
#     date_to: Optional[date] = Query(None, description="Конечная дата фильтрации (в формате YYYY-MM-DD)", example="2025-05-30"),
#     debt_id: int = Query(None, description="id долга", example=1),
#     project_id: int = Query(None, description="id долга", example=1)                    
#       ):
#     """
#     Параметры:
#     - limit: количество возвращаемых записей (по умолчанию 100)
#     - offset: смещение (по умолчанию 0)
#     - order_by: порядок сортировки ('asc' или 'desc')
#     - target_id: id цели
#     - debt_id: id долга
#     - date_from: начальная дата для фильтрации
#     - date_to: конечная дата для фильтрации
#     """
#     logger.info("Запрос на получение операций на повторение")
    
#     try:
#         # Сначала формируем базовый запрос
#         query = db.query(OperationsRepeat).options(
#             joinedload(OperationsRepeat.transaction)
#         )
#         if current_user:
#             query = query.filter(OperationsRepeat.user_id == current_user.user_id)
#         # Применяем фильтры (если параметры переданы)
#         if target_id:
#             query = query.filter(OperationsRepeat.target_id == target_id)
#         if debt_id:
#             query = query.filter(OperationsRepeat.debt_id == debt_id)
        
#         # Фильтрация по дате
#         if date_from:
#             query = query.filter(OperationsRepeat.created_at >= date_from)
#         if date_to:
#             # Добавляем 1 день к date_to, чтобы включить все записи за указанный день
#             next_day = date_to + timedelta(days=1)
#             query = query.filter(OperationsRepeat.created_at < next_day)
        
#         # Сортировка
#         if order_by.lower() == "asc":
#             query = query.order_by(OperationsRepeat.created_at.asc())
#         else:
#             query = query.order_by(OperationsRepeat.created_at.desc())
        
#         # Выполняем запрос и получаем результат
#         total = query.count()
#         reapits = query.offset(offset).limit(limit).all()  
#         logger.info(f"Найдено {len(reapits)} операций")
        
#         if not reapits:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Операции на повторение не найдены"
#             )
        
#         return {
#             "total": total,
#             'reapits': reapits
#         }
        
#     except SQLAlchemyError as e:
#         logger.error(f"Ошибка базы данных: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Произошла ошибка при получении данных"
#         )


# @router.post('/',
#               summary="Добавить операцию на повтор",
#               response_model=OperationsResponse,
#               status_code=status.HTTP_201_CREATED
#               )

# def add_operation_to_reapit(
#         operationsrepeat: CreateOperationsRepeat,
#         current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
#         db: Session = Depends(get_db) 
#     ):
#         """
#         - interval типы: day, week, month, year
#         - type: target, debt, limit, transaction
#         """
#         try:
#             logger.info(f"Добавить операцию на повтор для user_id: {current_user.user_id}")
#             # Сравнение типа операции
#             if not operationsrepeat.transaction_id:
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail="Нужно указать id транзакции"
#                 )
             
#             transaction:Transactions = db.query(Transactions).filter(Transactions.id == operationsrepeat.transaction_id).first()
#             if not transaction:
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail="Транзакция не найдена"
#                 )
#              # # Конвертируем объект SQLAlchemy в dict и затем в JSON
#             repeat_dict = jsonable_encoder(transaction)
#             repeat_json = json.dumps(repeat_dict, ensure_ascii=False, indent=2)
#             # Создаем запись о повторении
#             new_repeat = OperationsRepeat(
#                 type=operationsrepeat.type,
#                 interval=operationsrepeat.interval,
#                 repeat_date=operationsrepeat.repeat_date,
#                 repeat_count=operationsrepeat.repeat_count,
#                 transaction_id = operationsrepeat.transaction_id,
#                 user_id=current_user.user_id
#             )
#             if transaction.debt_id:
#                 logger.info(f"Транзакция с debt_id: {transaction.debt_id}")
#                 new_repeat.debt_id = transaction.debt_id
#             if transaction.target_id:
#                 logger.info(f"Транзакция с target_id: {transaction.target_id}")
#                 new_repeat.target_id = transaction.target_id
#             # # Логируем весь объект в JSON формате
#             logger.info(f"Создаваемый объект OperationsRepeat:\n{repeat_json}")
           
#             db.add(new_repeat)
#             db.commit()
#             db.refresh(new_repeat)
#             return new_repeat
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Ошибка при создании операции: {str(e)}"
#             )
          