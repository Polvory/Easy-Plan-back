from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from sqlalchemy.orm import Session
from typing import List
from db import SessionLocal
from models import Targets
from auth.auth import guard_role, TokenPayload
from datetime import datetime
import logging

from schemas import CreateTarget, TargetsOut, TargetUpdate

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/targets",
    tags=["targets"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", summary="Получить все цели", response_model=List[TargetsOut])
def get_targets(
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db),
):
    targets = db.query(Targets).filter(Targets.user_id == current_user.user_id).all()
    return targets

@router.post("/", summary="Создать цель", response_model=TargetsOut, status_code=status.HTTP_201_CREATED)
def create_target(
    target: CreateTarget,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"],  limit_key="goals")),
    db: Session = Depends(get_db),
):
    try:
        new_target = Targets(
            name=target.name,
            balance_target=target.balance_target,
            balance=target.balance,
            date_end=target.date_end,
            completed=target.completed,
            account_id=target.account_id,
            svg=target.svg,
            user_id=current_user.user_id
        )
        
        db.add(new_target)
        db.commit()
        db.refresh(new_target)
        return new_target
    except Exception as e:
        db.rollback()
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=f"Ошибка при создании цели:{e}")

@router.put("/", summary="Обновить цель", response_model=TargetsOut)
def update_target(
    target_id: int,
    update_data: TargetUpdate,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db),
):
    target = db.query(Targets).filter(Targets.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    if target.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав для редактирования этой цели")

    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(target, field, value)
    target.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(target)
    return target

@router.delete("/", summary="Удалить цель", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(
    target_id: int,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db),
):
    target = db.query(Targets).filter(Targets.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    if target.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав для удаления этой цели")

    db.delete(target)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
