import os
import datetime 
from typing import List, Optional
from sqlalchemy import create_engine, ForeignKey, String, Integer, Boolean, DateTime 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship 

## Configuration for Database Connection 
# SQLite uses a file-based database, so we just need a URL pointing to the file.
# The `///` indicates a file path relative to the current directory.
DATABASE_URL = "sqlite:///blog.db"


# -- Declrative Base Class --
class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""
    pass 

## -- ORM Models -- 
class User(Base):
    """ORM Model for User Table."""
    __tablename__ = "users" # Mapping to the 'users' table

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    posts: Mapped[List["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, email={self.email!r})"
    
    
# Defining a helper funciton to setup the database
class Post(Base):
    """ORM Model for Post Table.""" 
    __tablename__ = "posts" # Maps this class to the "posts" table

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    published_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    author: Mapped['User'] = relationship(back_populates='posts')

    def __repr__(self) -> str:
        return f"Post(id={self.id!r}, title={self.title!r}, user_id={self.user_id!r})"
    

# Defining a helper funciton to setup the database
def setup_orm_database(db_url: str):
    """Setting up ORM Database.""" 
    print(f"Setting up ORM Database at {db_url}...")
    engine = create_engine(db_url, echo=True)

    try:
        # We can drop all tabls if already exists.
        Base.metadata.drop_all(engine)
        # Create all table defined in the Base.metadata 
        Base.metadata.create_all(engine)
        print(f"Database setup with all tables in {db_url} successfully.")
    except Exception as e:
        print(f"Error setting up database: {e}")
    finally:
        if engine:
            engine.dispose()

if __name__ == "__main__":
    setup_orm_database(DATABASE_URL)