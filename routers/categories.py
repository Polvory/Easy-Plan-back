from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from typing import List
from models import TransactionsTypeEnum, User, Categories  # Добавляем импорт модели Transaction
from db import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy.orm import load_only
from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional
from schemas import CategoriesResponse, CreateCategori, UpdateCategoryRequest
from fastapi.responses import JSONResponse
from auth.auth import  guard_role, TokenPayload
# from guard.guard import get_current_user, TokenPayload
import logging
# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Добавьте в начало файла


# Создаём роутер для пользователей
router = APIRouter(
    prefix="/categories",
    tags=["categories"],  # Группировка в Swagger UI
)

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




@router.get("/all", 
            summary="Получить категории (user/admin)",
            response_model=List[CategoriesResponse],  # Используем новую модель
            status_code=status.HTTP_200_OK)
async def get_all_categories(
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    include_base: bool = Query(
        False,
        description="Если True, то вернет все категории + базовые."
        "Если False, то вернет только пользовательские категории."      
        ,
        example=True
    ),
    name_filter: str = Query(
        None,
        description="Если задано, то фильтрует категории по имени."
    ),
    db: Session = Depends(get_db),
    
):
    try:
        logger.info(f"Получение категорий для user_id: {current_user}")
        query = db.query(Categories)
        logger.info(query)
        user_id = current_user.user_id
        
        
        if user_id is not None:
            # Если указан user_id
            if include_base:
                query = query.filter(
                    (Categories.user_id == user_id) | 
                    (Categories.type == 'admin')
                )
            else:
                query = query.filter(Categories.user_id == user_id)
                
        if name_filter:
            query = query.filter(Categories.name.ilike(f"%{name_filter}%"))  # Фильтрация по имени
            
        categories = query.options(
            load_only(
                Categories.id,
                Categories.name,
                Categories.icon,
                Categories.color,
                Categories.svg,
                Categories.type,
                Categories.user_id,
                Categories.created_at,
                Categories.updated_at
            )
        ).order_by(Categories.name).all()
        
        return categories
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении категорий: {str(e)}"
        )
        
@router.post("/add", summary="Добавить категорию (admin/user)")
async def add_category(
    category: CreateCategori,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    """
    Добавляет новую категорию.
    """
    try:
        logger.info(f"Добавление категории для user_id: {current_user.role} {current_user.user_id}")
        # # Создаем базовый объект категории
        logger.info(category)
        new_category = Categories(
            name=category.name,
            icon=category.icon if category.icon else None,
            color=category.color,
            svg=category.svg if category.svg else None,
            type=current_user.role,
            user_id=current_user.user_id,
            moded=TransactionsTypeEnum(category.moded),
        )
        user = db.query(User).filter(User.id == current_user.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Указанный пользователь не найден"
            )
            
        # Сохраняем категорию
        db.add(new_category)
        db.commit()
        db.refresh(new_category)

        # Формируем ответ
        response_data = {
            "id": new_category.id,
            "name": new_category.name,
            "type": new_category.type,
            "user_id": new_category.user_id,
            "message": "Категория успешно создана"
        }

        return response_data 
    except HTTPException:
        # Перевыбрасываем уже обработанные HTTP исключения
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании категории: {str(e)}"
        )

@router.patch("/{category_id}", 
             summary="Обновить категорию (user/admin)",
             response_model=CategoriesResponse)
async def update_category(
    category_id: int,
    update_data: UpdateCategoryRequest,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    """
    Обновляет данные категории.
    - Можно обновлять отдельные поля (name, icon, color, svg)
    - Возвращает обновленную категорию
    """
    try:
        logger.info(f"Обновляем категории для user_id: {current_user.role} {current_user.user_id}")
        # Получаем категорию из БД
        category = db.query(Categories).filter(Categories.id == category_id).first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Категория не найдена"
            )
        
        # Проверка принадлежности пользователю (если передан user_id)
        if current_user.user_id is not None:
            if category.user_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Категория не принадлежит указанному пользователю"
                )
        
        # Обновляем только переданные поля
        if update_data.name is not None:
            category.name = update_data.name
        if update_data.icon is not None:
            category.icon = update_data.icon
        if update_data.color is not None:
            category.color = update_data.color
        if update_data.svg is not None:
            category.svg = update_data.svg
        if update_data.moded is not None:
            category.moded = update_data.moded
        
        db.commit()
        db.refresh(category)
        
        return category
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении категории: {str(e)}"
        )
        


@router.delete("/{category_id}", 
              summary="Удалить категорию (user/admin)",
              status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_category(
    category_id: int,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    """
    Требования:
    - Категория должна принадлежать указанному пользователю
    """
    try:
        logger.info(f"Удалить категорию для user_id: {current_user.role} {current_user.user_id}")
        
        category = db.query(Categories)\
                   .filter(
                       Categories.id == category_id,
                       Categories.user_id == current_user.user_id
                   ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Категория не найдена или не принадлежит пользователю"
            )

        db.delete(category)
        db.commit()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении категории: {str(e)}"
        )



     
