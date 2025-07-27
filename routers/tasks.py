from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from routers.transactions import create_transaction, delete_transaction
from routers.project import update_progress
import json
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import contains_eager
from db import SessionLocal
from models import Project, Tasks, Transactions
from auth.auth import TokenPayload, guard_role
from schemas import CreateTransaction, TaskCreate, TaskUpdate, TaskOut, TaskUpdateOut

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],  # Группировка в Swagger UI
)

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

def get_task_by_user_id(task_id, db):
    """
    Получение лимитов по user_id
    """
    return db.query(Tasks).filter(Tasks.id == task_id).first()


@router.get(
    "/by-project/{project_id}",
    summary="Получить задачи по проекту",
    response_model=List[TaskOut],
    status_code=status.HTTP_200_OK
)
def get_tasks_by_project(
    project_id: int,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    logger.info(f"[get_tasks_by_project] user_id={current_user.user_id}, project_id={project_id}")
    try:
        tasks = db.query(Tasks).options(joinedload(Tasks.transaction)).filter(Tasks.project_id == project_id).all()
        if not tasks:
            raise HTTPException(status_code=404, detail="Задачи не найдены")
        return tasks
    except SQLAlchemyError as e:
        logger.error(f"[get_tasks_by_project] DB error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении задач")


from datetime import datetime
from sqlalchemy import or_, and_
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@router.get('/current',
            summary="Актуальные задачи (незавершенные, начиная от текущей даты)")
def current_tasks(
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db),
    limit: int = 10,
    include_completed: bool = False
):
    try:
        user_id = current_user.user_id
        current_date = datetime.now()

        # Загружаем задачи вместе с проектами (avoid N+1 problem)
        tasks = db.query(Tasks).join(Project).filter(
            Project.user_id == user_id,
            Tasks.date_end >= current_date,
            Tasks.completed == include_completed
        ).options(joinedload(Tasks.project)).order_by(Tasks.date_end.asc()).limit(limit).all()

        # Формируем ответ с добавлением цвета проекта
        response = []
        for task in tasks:
            task_data = task.__dict__
            task_data['project_color'] = task.project.color  # Добавляем цвет проекта
            response.append(task_data)

        return response

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении задач")
    
    
@router.post(
    "/",
    summary="Создать задачу",
    # response_model=TaskOut
)
async def create_task(
    task_data: TaskCreate,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"[create_task] user_id={current_user.user_id}, data={task_data}")
        print(task_data)
        task = Tasks(**task_data.dict())
        db.add(task)
        db.commit()
        db.refresh(task)
        await update_progress(task_data.project_id, current_user.user_id, db)
        return task_data
    except SQLAlchemyError as e:
        logger.error(f"[create_task] DB error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при создании задачи")



@router.put("/{task_id}", response_model=TaskUpdateOut, description="""
    Обновляет данные задачи и автоматически управляет связанной транзакцией:
    
    - При установке completed=true:
      * Если переданы sum, moded и account_id - создает новую транзакцию
      * Если уже есть транзакция - сначала удаляет старую
      * Возвращает статус создания транзакции
    
    - При установке completed=false:
      * Удаляет связанную транзакцию (если существует)
    
    Требования для создания транзакции:
    - Поля sum, moded и account_id должны быть заполнены
    - Либо в теле запроса, либо в сохраненной задаче
    """,)
async def update_task(
    task_id: int,
    update_data: TaskUpdate,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"[update_task] user_id={current_user.user_id}, task_id={task_id}, data={update_data}")
        
        task = db.query(Tasks).options(joinedload(Tasks.transaction)).join(Project).filter(
            Tasks.id == task_id,
            Project.user_id == current_user.user_id
        ).first()

        if not task:
            logger.warning(f"[update_task] Задача не найдена: task_id={task_id}")
            raise HTTPException(status_code=404, detail="Задача не найдена")

        # Инициализируем статус транзакции
        transaction_status = "Транзакция не требовалась"
        new_transaction = None

        # Получаем данные для транзакции
        account_id = update_data.account_id if update_data.account_id is not None else task.account_id
        sum_value = update_data.sum if update_data.sum is not None else task.sum
        moded_value = update_data.moded if update_data.moded is not None else task.moded

        if update_data.completed:
            if all([moded_value, account_id, sum_value]):
                logger.info('Данных для транзакции достаточно')
                transaction_data = CreateTransaction(
                    user_id=current_user.user_id,
                    sum=sum_value,
                    moded=moded_value,
                    repeat_operation=False,
                    account_id=account_id,
                    task_id=task.id,
                    transaction_data = None
                )

                if task.transaction:
                    logger.info('Транзакция существует, удаляем')
                    await delete_transaction(
                        transaction_id=task.transaction.id,
                        current_user=current_user,
                        db=db
                    )
                    transaction_status = "Старая транзакция удалена, "

                new_transaction = await create_transaction(
                    transaction_data=transaction_data,
                    current_user=current_user,
                    db=db
                )
                transaction_status += "Новая транзакция создана"
            else:
                transaction_status = "Не хватает данных для транзакции"
                logger.info('Задача выполнена, но не хватает данных для транзакции')
        else:
            if task.transaction:
                logger.info('Задача не выполнена, удаляем транзакцию')
                await delete_transaction(
                    transaction_id=task.transaction.id,
                    current_user=current_user,
                    db=db
                )
                transaction_status = "Транзакция удалена (задача не выполнена)"

        # Обновляем задачу
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(task, field, value)
        
        db.commit()
        db.refresh(task)
        await update_progress(task.project_id, current_user.user_id, db)

        return {
            "task": task,
            "transaction_status": transaction_status,
        }

    except SQLAlchemyError as e:
        logger.error(f"[update_task] DB error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении задачи: {str(e)}")

@router.delete(
    "/{task_id}",
    summary="Удалить задачу"
)
async def delete_task(
    task_id: int,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"[delete_task] user_id={current_user.user_id}, task_id={task_id}")
        task = db.query(Tasks).options(joinedload(Tasks.transaction)).join(Project).filter(
                Tasks.id == task_id,
                Project.user_id == current_user.user_id
            ).first()
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        loggger_json(task)
        if task.transaction:
                logger.info('Транзакция уже существует, удаляем старую создаем новую')
                delete_transaction_res = await delete_transaction(
                    transaction_id = task.transaction.id,
                    current_user=current_user,
                    db=db
                )
                if delete_transaction_res:
                    logger.info('Удалили транзакцию')
        db.delete(task)
        db.commit()
        await update_progress(task.project_id, current_user.user_id, db)
        
        logger.info(f"[delete_task] Успешно удалена: task_id={task_id}")
        return {"detail": "Задача удалена"}
    except SQLAlchemyError as e:
        logger.error(f"[delete_task] DB error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при удалении задачи")
