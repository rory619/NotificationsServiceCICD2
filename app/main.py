from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import Base

from fastapi import Depends, HTTPException, status, Response 
from sqlalchemy.orm import Session 
from sqlalchemy import select 
from sqlalchemy.exc import IntegrityError 
from sqlalchemy.orm import selectinload 
from app.database import SessionLocal 
from app.models import NotificationsDB
from app.schemas import ( NotificationCreate, NotificationRead ) 

#Replacing @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine) 
    yield

app = FastAPI(lifespan=lifespan)
# CORS (add this block)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # dev-friendly; tighten in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine),

def get_db(): 
    db = SessionLocal() 
    try: 
        yield db 
    finally: 
        db.close() 
 
def commit_or_rollback(db: Session, error_msg: str): 
    try: 
        db.commit() 
    except IntegrityError: 
        db.rollback() 
        raise HTTPException(status_code=409, detail=error_msg) 
 
@app.get("/health") 
def health(): 
    return {"status": "ok"} 
 
#Notifications
@app.post("/api/notifications", response_model=NotificationRead, status_code=201, summary="Create new notification") 
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)): 
    db_notif = NotificationsDB(**payload.model_dump()) 
    db.add(db_notif) 
    commit_or_rollback(db, "Notification create failed") 
    db.refresh(db_notif) 
    return db_notif 
 
@app.get("/api/notifications", response_model=list[NotificationRead]) 
def list_notifications(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)): 
    stmt = select(NotificationsDB).order_by(NotificationsDB.id).limit(limit).offset(offset) 
    return db.execute(stmt).scalars().all() 
 

@app.get(
    "/api/notifications/{notification_id}",response_model=NotificationRead,summary="Get a single notification",)
def get_notification(notification_id: int,db: Session = Depends(get_db),):
    notif = db.get(NotificationsDB, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif

@app.put(
    "/api/notifications/{notification_id}",response_model=NotificationRead,summary="Update an existing notification (full replace)",)
def update_notification(notification_id: int,payload: NotificationCreate,db: Session = Depends(get_db),):
    notif = db.get(NotificationsDB, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.user_id = payload.user_id
    notif.channel = payload.channel
    notif.message = payload.message

    commit_or_rollback(db, "Notification update failed")
    db.refresh(notif)
    return notif

@app.delete("/api/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(notification_id: int,db: Session = Depends(get_db),) -> Response:
    notif = db.get(NotificationsDB, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(notif)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)