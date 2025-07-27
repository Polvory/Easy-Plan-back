from datetime import date, timedelta
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from sqlalchemy.orm import joinedload
import json
from db import SessionLocal
from models import Project, Tasks, User
from auth.auth import TokenPayload, guard_role
from schemas import ProjectCreate, ProjectOut, ProjectResponse, ProjectResponseWithTotal, ProjectTaskOut, ProjectUpdate
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func  # Импорт функции для агрегации
from sqlalchemy.orm import selectinload
# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём роутер для проектов
router = APIRouter(
    prefix="/projects",
    tags=["projects"],  # Группировка в Swagger UI
)


def loggger_json(data):
    """
    Функция для логирования данных в формате JSON.
    """
    try:
        data_dict = jsonable_encoder(data)
        data_json = json.dumps(data_dict, ensure_ascii=False, indent=2)
        logger.info(f"JSON:\n{data_json}")
        return data_json
    except TypeError as e:
        logger.error(f"Ошибка при преобразовании данных в JSON: {e}")

@router.get(
    "/by-user",
    summary="Получить список проектов пользователя",
    response_model=ProjectResponseWithTotal,
    status_code=status.HTTP_200_OK
)
def get_projects_by_user(
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    limit: int = Query(100, gt=0, le=1000),
    offset: int = Query(0, ge=0),
    order_by: str = Query("desc", description="Порядок сортировки (asc/desc)"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    completed:bool =  Query( description="Готовы", example=False),
):
    logger.info(f"[get_projects_by_user] user_id={current_user.user_id}")
    try:
        # Базовый запрос для подсчета общего количества
        count_query = db.query(Project).options(selectinload(Project.tasks)).filter(Project.user_id == current_user.user_id)

        # Основной запрос с агрегациями
        query = db.query(
            Project,
            func.count(Tasks.id).label('tasks_count'),
            func.coalesce(func.sum(Tasks.sum), 0).label('total_sum')
        ).outerjoin(
            Tasks, Tasks.project_id == Project.id
        ).filter(
            Project.user_id == current_user.user_id,
            Project.completed == completed
        ).group_by(
            Project.id
        ).options(selectinload(Project.tasks))  # Загружаем связанные задачи

        # Фильтры по дате
        if date_from:
            query = query.filter(Project.created_at >= date_from)
            count_query = count_query.filter(Project.created_at >= date_from)
        if date_to:
            next_day = date_to + timedelta(days=1)
            query = query.filter(Project.created_at < next_day)
            count_query = count_query.filter(Project.created_at < next_day)

        # Общее количество
        total = count_query.count()

        # Сортировка
        if order_by.lower() == "asc":
            query = query.order_by(Project.created_at.asc())
        else:
            query = query.order_by(Project.created_at.desc())

        # Пагинация
        projects_data = query.offset(offset).limit(limit).all()

        if not projects_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Проекты не найдены"
            )

        # Формируем результат
        projects = []
        for project, tasks_count, total_sum in projects_data:
            project_dict = project.__dict__.copy()
            project_dict['total'] = tasks_count
            project_dict['total_sum'] = total_sum
            project_dict['tasks'] = [ProjectTaskOut.from_orm(task) for task in project.tasks]
            projects.append(project_dict)

        logger.info(f"Найдено {len(projects)} проектов из {total}")

        return {
            "total": total,
            "projects": projects,
        }

    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при получении данных"
        )



@router.post(
    "/",
    summary="Создать новый проект",
    response_model=ProjectOut
)
def create_project(
    project_data: ProjectCreate,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"[create_project] user_id={current_user.user_id}, data={project_data}")
        project = Project(
            name=project_data.name,
            color=project_data.color,
            completed=project_data.completed,
            progress=project_data.progress,
            user_id=current_user.user_id
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    except SQLAlchemyError as e:
        logger.error(f"[create_project] DB error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании проекта"
        )

@router.put(
    "/{project_id}",
    summary="Обновить проект",
    response_model=ProjectOut
)
def update_project(
    project_id: int,
    update_data: ProjectUpdate,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    """
        Передаем только те значения, которые нужно обновить.
        Обновляет данные проекта по ID.
        - Возвращает обновленный проект
        - Если проект не найден, возвращает 404
    """
    try:
        logger.info(f"[update_project] user_id={current_user.user_id}, project_id={project_id}, data={update_data}")
        project = db.query(Project).filter_by(id=project_id, user_id=current_user.user_id).first()
        if not project:
            logger.warning(f"[update_project] Проект не найден: project_id={project_id}")
            raise HTTPException(status_code=404, detail="Проект не найден")




        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(project, field, value)

        db.commit()
        db.refresh(project)
        return project
    except SQLAlchemyError as e:
        logger.error(f"[update_project] DB error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении проекта"
        )

@router.delete(
    "/{project_id}",
    summary="Удалить проект"
)
def delete_project(
    project_id: int,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"[delete_project] user_id={current_user.user_id}, project_id={project_id}")
        project = db.query(Project).filter_by(id=project_id, user_id=current_user.user_id).first()
        if not project:
            logger.warning(f"[delete_project] Проект не найден: project_id={project_id}")
            raise HTTPException(status_code=404, detail="Проект не найден")

        db.delete(project)
        db.commit()
        logger.info(f"[delete_project] Успешно удалён: project_id={project_id}")
        return {"detail": "Проект удален"}
    except SQLAlchemyError as e:
        logger.error(f"[delete_project] DB error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении проекта"
        )
        
def calculate_completion_percentage(tasks):
    """
    Вычисляет процент выполненных задач
    
    :param tasks: Список задач (как в вашем примере)
    :return: Процент выполненных задач (0-100)
    """
    if not tasks:
        return 0  # Если список пуст
    
    completed_count = sum(1 for task in tasks if task.get('completed') is True)
    total_count = len(tasks)
    
    percentage = (completed_count / total_count) * 100
    return round(percentage, 2)  # Округляем до 2 знаков после запятой

async def update_progress(project_id,user_id, db):
        logger.info(project_id)
        project:ProjectResponse = db.query(Project).filter_by(id=project_id, user_id=user_id).options(joinedload(Project.tasks)).first()
        if not project.tasks:
             logger.log('Нет таксов')
        else:
            
            count_completed = 0
            total_tasks = len(project.tasks)  # Общее количество задач
            # completion_percent = loggger_json(project.tasks)
            for task in project.tasks:
                    if task.completed == True:
                        count_completed += 1
                # if task['completed'] == True:
                #     print(task['id'])
            # Вычисляем процент выполненных (с округлением до 2 знаков)
            completion_percent = round((count_completed / total_tasks) * 100, 1) if total_tasks > 0 else 0

            print(f"Всего задач: {total_tasks}")
            print(f"Выполнено: {count_completed} ({completion_percent}%)")
            project.progress = completion_percent
            if completion_percent == 100:
                project.completed = True
            else:
                project.completed = False
            db.commit()
            db.refresh(project)
            return True
        
        return False