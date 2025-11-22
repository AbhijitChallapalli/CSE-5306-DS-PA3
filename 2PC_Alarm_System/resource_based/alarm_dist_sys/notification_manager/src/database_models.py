from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from database import Base

class NotificationDB(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, index=True)
    message = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
