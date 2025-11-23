from fastapi import FastAPI, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from pydantic_models import Message
from database_models import NotificationDB
from database import SessionLocal, init_db

app = FastAPI(title="Notification Manager")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
def root():
    return {"message": "Notification Manager running"}

@app.get("/notifications")
async def get_notifcations(user_id: int | None = None, db: Session = Depends(get_db)):
    notifications = db.query(NotificationDB)

    if user_id:
        notifications = notifications.filter(NotificationDB.user_id == user_id)
    
    return notifications.all()

@app.post("/notifications/{user_id}")
async def notify_user(user_id: int, msg: Message, db: Session = Depends(get_db)):
    new_notif = NotificationDB(user_id=user_id, message=msg.message)
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)

    print(f"[Notification Manager] Added notification \"{msg.message}\" to database {user_id}")

    return {"status": "queued"}

@app.delete("/notifications")
async def delete_notification(user_id: int = Query(...), db: Session = Depends(get_db)):
    # Bulk delete all notifications corresponding to the user
    deleted_count = db.query(NotificationDB).filter(NotificationDB.user_id == user_id).delete(synchronize_session=False)
    db.commit()

    print(f"[Alarm Manager] Deleted notifications under {user_id}")
    return {"deleted": deleted_count}

@app.delete("/notifications/{notif_id}")
async def delete_notification(notif_id: int, db: Session = Depends(get_db)):
    notification = db.query(NotificationDB).filter(NotificationDB.id == notif_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(notification)
    db.commit()

    print(f"[Notification Manager] Deleted notificaion: id={notification.id}, message={notification.message}")
    return {"deleted_id": notif_id}
