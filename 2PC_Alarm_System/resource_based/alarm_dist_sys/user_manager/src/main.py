from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic_models import User, UserOut, UpdateUser
from database_models import UserDB
from database import SessionLocal, init_db
from utility import delete_alarms_for_user, delete_notifications_for_user

app = FastAPI(title="User Manager")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return {"message": "User Manager is running"}

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(id=user.id, username=user.username)

@app.post("/users/register")
def create_user(user: User, db: Session = Depends(get_db)):
    if db.query(UserDB).filter(UserDB.username == user.username).first():
        raise HTTPException(status_code=409, detail="User account already exists")

    password_hash = pwd_context.hash(user.password)
    new_user = UserDB(username=user.username, password_hash=password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserOut(id=new_user.id, username=new_user.username)

@app.post("/users/authenticate")
def authenticate_user(user: User, db: Session = Depends(get_db)):
    user_db_entry = db.query(UserDB).filter(UserDB.username == user.username).first()
    if not user_db_entry:
        raise HTTPException(status_code=404, detail="User account not found")
    if not pwd_context.verify(user.password, user_db_entry.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return UserOut(id=user_db_entry.id, username=user_db_entry.username)

@app.put("/users/{user_id}")
def update_user(user_id: int, updated_fields: UpdateUser, db: Session = Depends(get_db)):
    user_db_entry = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user_db_entry:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in updated_fields.dict(exclude_unset=True).items():
        setattr(user_db_entry, key, value)
    db.commit()
    db.refresh(user_db_entry)

    return user_db_entry

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    delete_alarms_for_user(user_id)
    delete_notifications_for_user(user_id)
    db.delete(user)
    db.commit()
        
