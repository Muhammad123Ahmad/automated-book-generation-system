import os
from datetime import datetime
from typing import List, Optional

from sqlalchemy import create_engine, ForeignKey, String, Text, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, scoped_session

# Use SQLite for now. Can be swapped for Supabase/Postgres connection string.
DB_URL = "sqlite:///book_gen.db"

engine = create_engine(DB_URL, echo=False)
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)

class Base(DeclarativeBase):
    pass

class Book(Base):
    __tablename__ = "books"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    # Status: PLANNING, WRITING_OUTLINE, REVIEWING_OUTLINE, WRITING_CHAPTERS, REVIEWING_CHAPTER, COMPLETED
    status: Mapped[str] = mapped_column(String(50), default="PLANNING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    outline: Mapped["Outline"] = relationship(back_populates="book", uselist=False, cascade="all, delete-orphan")
    chapters: Mapped[List["Chapter"]] = relationship(back_populates="book", cascade="all, delete-orphan", order_by="Chapter.chapter_number")

class Outline(Base):
    __tablename__ = "outlines"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    content: Mapped[str] = mapped_column(Text)
    # Status: DRAFT, WAITING_FOR_REVIEW, APPROVED
    status: Mapped[str] = mapped_column(String(50), default="DRAFT")
    editor_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    book: Mapped["Book"] = relationship(back_populates="outline")

class Chapter(Base):
    __tablename__ = "chapters"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    chapter_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Status: PENDING, DRAFT, WAITING_FOR_REVIEW, APPROVED
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    editor_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    book: Mapped["Book"] = relationship(back_populates="chapters")

def init_db():
    """Initialize the database tables."""
    Base.metadata.create_all(engine)

def get_session():
    """Get a new database session."""
    return Session()
