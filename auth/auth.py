from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from datetime import datetime, timedelta
from db import SessionLocal
from models import User
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from models import CategoriTypeEnum,  LanguageTypeEnum # Импортируйте вашу модель пользователя
import logging
# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Конфигурация
SECRET_KEY = "your-secret-key-here"
REFRESH_SECRET_KEY = "your-refresh-secret-key"  # Желательно другой ключ
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Pydantic-модель токенов
class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    user_id: int
    role:CategoriTypeEnum
    language: LanguageTypeEnum

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: TokenPayload) -> str:
    try:
        logger.info(data)
        expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
                "user_id": data["user_id"],
                "role": data["role"],  # ❌ <Enum>
                "language": data["language"],  # ❌ <Enum>
                "exp": expires
            }
        return jwt.encode(
            payload, 
            SECRET_KEY, 
            algorithm=ALGORITHM)
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def create_refresh_token(data: TokenPayload) -> str:
    try:
        logger.info(data)
        expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
                    "user_id": data["user_id"],
                    "role": data["role"],  # ❌ <Enum>
                    "language": data["language"],  # ❌ <Enum>
                    "exp": expires
                }
        return jwt.encode(payload, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def login(data: TokenPayload):  # Пример: передаётся user_id, обычно тут логика проверки логина/пароля
    try:
        logger.info(data)
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)
        logger.info(f"Access token: {access_token}")
        logger.info(f"Refresh token: {refresh_token}")
        logger.info(f"Tokens created successfully")
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token
        )
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def guard_role(required_roles: Optional[List[str]] = None,  
            #    db: Session = Depends(get_db)
               ):
    async def dependency(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
        ) -> TokenPayload:
        token = credentials.credentials
        logger.info(f"Token: {token}")
        
        try:
            payload: Dict[str, Any] = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            logger.info(f"Decoded payload: {payload}")
            payload["exp"] = datetime.fromtimestamp(payload["exp"])


            user = TokenPayload(**payload)
             # Получение пользователя из БД
            user_in_db:User = db.query(User).filter(User.id == user.user_id).first()
            if not user_in_db:
                raise HTTPException(status_code=401, detail="User not found")

            
            user_actual = TokenPayload(
                user_id=user_in_db.id,
                role=user_in_db.role,
                language=user_in_db.language
            )
            
            logger.info(f"User from DB: {user_actual}")
          
            if required_roles and user.role not in required_roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            
            return user_actual

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    return dependency
        
