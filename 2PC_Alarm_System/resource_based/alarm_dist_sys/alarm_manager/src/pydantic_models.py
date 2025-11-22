from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class Alarm(BaseModel):
    user_id: int
    message: str
    time: datetime
    status: Optional[str] = "pending" 

class UpdateAlarm(BaseModel):
    message: Optional[str] = None
    time: Optional[datetime] = None
    status: Optional[str] = None