from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from typing import List
from models import User, Categories  # Добавляем импорт модели Transaction
from db import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy.orm import load_only
from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional
from schemas import CategoriesResponse, CreateCategori, UpdateCategoryRequest, UpdateAdminCategoryRequest
from fastapi.responses import JSONResponse
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
            summary="Получить категории",
            response_model=List[CategoriesResponse],  # Используем новую модель
            status_code=status.HTTP_200_OK)
async def get_all_categories(
    user_id: Optional[int] = Query(
        None,
        description="ID пользователя для фильтрации категорий. "
                   "Если не указан - возвращаются все категории",
        example=1
    ),
    include_base: bool = Query(
        False,
        description="Включить базовые категории (type='admin') вместе с пользовательскими. "
                   "Если запросить без user_id вернуться только базовые",
        example=True
    ),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Categories)

        if user_id is not None:
            # Если указан user_id
            if include_base:
                query = query.filter(
                    (Categories.user_id == user_id) | 
                    (Categories.type == 'admin')
                )
            else:
                query = query.filter(Categories.user_id == user_id)
        else:
            # Если user_id не указан - только админские категории
            query = query.filter(Categories.type == 'admin')

        # Явно указываем какие отношения загружать (исключаем user)
        # Затем используйте просто load_only() без sqlalchemy.
       # Правильное использование load_only с атрибутами модели
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


@router.patch("/{category_id}", 
             summary="Обновить категорию",
             response_model=CategoriesResponse)
async def update_category(
    category_id: int,
    update_data: UpdateCategoryRequest,
    db: Session = Depends(get_db)
):
    """
    Обновляет данные категории.
    
    - Если передан user_id, проверяем что категория принадлежит этому пользователю
    - Можно обновлять отдельные поля (name, icon, color, svg)
    - Возвращает обновленную категорию
    """
    try:
        # Получаем категорию из БД
        category = db.query(Categories).filter(Categories.id == category_id).first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Категория не найдена"
            )
        
        # Проверка принадлежности пользователю (если передан user_id)
        if update_data.user_id is not None:
            if category.user_id != update_data.user_id:
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
        
        db.commit()
        db.refresh(category)
        
        return category
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении категории: {str(e)}"
        )
        
@router.patch("/admin/{category_id}", 
             summary="Обновить админскую категорию",
             response_model=CategoriesResponse)
async def update_admin_category(
    category_id: int,
    update_data: UpdateAdminCategoryRequest,
    db: Session = Depends(get_db)
):
    """
    Обновляет данные админской категории (type='admin').
    
    Требования:
    - Категория должна быть админской (type='admin')
    - Можно обновлять отдельные поля (name, icon, color, svg)
    - Не требует привязки к пользователю (user_id=None)
    """
    try:
        # Получаем категорию из БД
        category = db.query(Categories)\
                   .filter(
                       Categories.id == category_id,
                       Categories.type == 'admin',
                       Categories.user_id == None
                   ).first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Админская категория не найдена или не является админской"
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
        
        db.commit()
        db.refresh(category)
        
        return category
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении админской категории: {str(e)}"
        )

@router.delete("/user/{category_id}", 
              summary="Удалить пользовательскую категорию",
              status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_category(
    category_id: int,
    user_id: int = Query(..., description="ID пользователя, который удаляет категорию"),
    db: Session = Depends(get_db)
):
    """
    Удаляет пользовательскую категорию (type='user').
    
    Требования:
    - Категория должна принадлежать указанному пользователю
    - Категория должна быть пользовательской (type='user')
    """
    try:
        category = db.query(Categories)\
                   .filter(
                       Categories.id == category_id,
                       Categories.type == 'user',
                       Categories.user_id == user_id
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
@router.delete("/admin/{category_id}", 
              summary="Удалить админскую категорию",
              status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Удаляет админскую категорию (type='admin').
    
    Требования:
    - Категория должна быть админской (type='admin')
    - Категория не должна быть привязана к пользователю (user_id=None)
    """
    try:
        category = db.query(Categories)\
                   .filter(
                       Categories.id == category_id,
                       Categories.type == 'admin',
                       Categories.user_id == None
                   ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Админская категория не найдена"
            )

        db.delete(category)
        db.commit()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении админской категории: {str(e)}"
        )

@router.post("/add", summary="Добавить категорию")
async def add_category(
    category: CreateCategori,
    db: Session = Depends(get_db)
):
    """
    Добавляет новую категорию.
    - Для type='user' обязателен user_id
    - Для type='admin' user_id не требуется
    """
    try:
        # Создаем базовый объект категории
        new_category = Categories(
            name=category.name,
            icon=category.icon,
            color=category.color,
            svg=category.svg,
            type=category.type,
            user_id=category.user_id if category.type == 'user' else None
        )

        # Валидация для пользовательских категорий
        if category.type == 'user':
            if not category.user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Для пользовательской категории необходимо указать user_id"
                )
            
            # Проверяем существование пользователя
            user = db.query(User).filter(User.id == category.user_id).first()
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
     
