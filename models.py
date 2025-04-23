from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    apple_id = Column(String(50), unique=True, nullable=False)
    tg_id = Column(String(255), unique=True, nullable=False)
    tg_name = Column(String(255), unique=True, nullable=False)
    premium = Column(Boolean, default=False)
    premium_start = Column(DateTime(timezone=True), nullable=True)
    premium_expiration = Column(DateTime(timezone=True), nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
