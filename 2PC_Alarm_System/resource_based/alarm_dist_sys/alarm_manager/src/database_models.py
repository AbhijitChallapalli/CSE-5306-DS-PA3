from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class AlarmDB(Base):
    __tablename__ = "alarms"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False)
    message = Column(String(255), nullable=False)
    time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(10), nullable=False, default="pending") # pending, late, notified