# ticketing_system/fastapi_api.py

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, selectinload
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from pydantic import BaseModel
import asyncio
from datetime import datetime
from typing import Optional 

# --- Konfigurasi Database ---
DATABASE_URL = "sqlite+aiosqlite:///db.sqlite3" 

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

class UserDB(Base):
    __tablename__ = "auth_user"
    id = Column(Integer, primary_key=True, index=True)
    password = Column(String)
    last_login = Column(DateTime)
    is_superuser = Column(Boolean)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    is_staff = Column(Boolean)
    is_active = Column(Boolean)
    date_joined = Column(DateTime)

    tickets_created = relationship("TicketDB", back_populates="created_by_user", foreign_keys="TicketDB.created_by_id")
    tickets_assigned = relationship("TicketDB", back_populates="assigned_to_user", foreign_keys="TicketDB.assigned_to_id")
    comments = relationship("CommentDB", back_populates="author_user")
    activities = relationship("TicketActivityDB", back_populates="actor_user")


class TicketDB(Base):
    __tablename__ = "tickets_ticket"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    status = Column(String)
    priority = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    assigned_to_id = Column(Integer, ForeignKey("auth_user.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("auth_user.id"), nullable=False)

    created_by_user = relationship("UserDB", back_populates="tickets_created", foreign_keys=[created_by_id])
    assigned_to_user = relationship("UserDB", back_populates="tickets_assigned", foreign_keys=[assigned_to_id])
    comments = relationship("CommentDB", back_populates="ticket_obj")
    activities = relationship("TicketActivityDB", back_populates="ticket_obj")

class CommentDB(Base):
    __tablename__ = "tickets_comment"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets_ticket.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("auth_user.id"), nullable=False)
    content = Column(Text)
    created_at = Column(DateTime)

    ticket_obj = relationship("TicketDB", back_populates="comments")
    author_user = relationship("UserDB", back_populates="comments")

class TicketActivityDB(Base):
    __tablename__ = "tickets_ticketactivity"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets_ticket.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("auth_user.id"), nullable=True)
    action = Column(String)
    timestamp = Column(DateTime)

    ticket_obj = relationship("TicketDB", back_populates="activities")
    actor_user = relationship("UserDB", back_populates="activities")


# --- Pydantic Schemas (untuk validasi data dan respons API) ---

class UserSchema(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_staff: bool
    
    class Config: # <--- PERBAIKAN: Ubah model_config menjadi class Config
        orm_mode = True # <--- PERBAIKAN: Ubah from_attributes menjadi orm_mode

class TicketSchema(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    created_by_user: UserSchema
    assigned_to_user: Optional[UserSchema]

    class Config: # <--- PERBAIKAN: Ubah model_config menjadi class Config
        orm_mode = True # <--- PERBAIKAN: Ubah from_attributes menjadi orm_mode

# --- Inisialisasi FastAPI ---
app = FastAPI()

# Dependency untuk mendapatkan sesi database
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --- Endpoint API ---

@app.get("/")
async def root():
    return {"message": "Selamat datang di FastAPI API untuk Sistem Ticketing"}

@app.get("/api/users/", response_model=list[UserSchema])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    """Mendapatkan daftar semua user."""
    from sqlalchemy.future import select
    result = await db.execute(select(UserDB).limit(100))
    users = result.scalars().all()
    return users

@app.get("/api/tickets/", response_model=list[TicketSchema])
async def get_all_tickets(db: AsyncSession = Depends(get_db)):
    """Mendapatkan daftar semua tiket."""
    from sqlalchemy.future import select
    from sqlalchemy.orm import selectinload # Re-import here if needed for clarity within function
    result = await db.execute(select(TicketDB).options(
        selectinload(TicketDB.created_by_user),
        selectinload(TicketDB.assigned_to_user)
    ).limit(100))
    tickets = result.scalars().all()
    return tickets

@app.get("/api/tickets/{ticket_id}", response_model=TicketSchema)
async def get_ticket_by_id(ticket_id: int, db: AsyncSession = Depends(get_db)):
    """Mendapatkan detail tiket berdasarkan ID."""
    from sqlalchemy.future import select
    from sqlalchemy.orm import selectinload # Re-import here if needed for clarity within function
    result = await db.execute(select(TicketDB).options(
        selectinload(TicketDB.created_by_user),
        selectinload(TicketDB.assigned_to_user)
    ).filter(TicketDB.id == ticket_id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan")
    return ticket