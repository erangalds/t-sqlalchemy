import os
import datetime 
from typing import List, Optional
from sqlalchemy import create_engine, ForeignKey, String, Integer, Boolean, DateTime 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship 

## Configuration for Database Connection 
# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "my_sqlalchemy_db"
DB_USER = "sqlalchemy"
DB_PASSWORD = "sqlalchemy_password"

# Create connection string (using psycopg3)
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# -- Declrative Base Class --
class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""
    pass 

## -- ORM Models -- 
class User(Base):
    """ORM Model for User Table."""
    __tablename__ = "users" # Mapping to the 'users' table

    # Columns mapped using Mapped and mapped_column() method 
    # primary_key=True and autoincrement=True for ID generation 
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    # Relationship to the Post model
    # back_populates links this relationship to the 'author' field in Post Table. 
    # cascade="all, delete-orphan" ensures that when a User is deleted, all related Posts are also deleted. 
    # If a Post is disassociated from a User, it will be deleted if it has no other associations. 
    # back_populates='author' allows bidirectional access between User and Post models.
    posts: Mapped[List["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, email={self.email!r})"
    

class Post(Base):
    """ORM Model for Post Table.""" 
    __tablename__ = "posts" # Maps this class to the "posts" table

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    # Define the foreign key column
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    published_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    # Relationship to the User model
    # Many-to-One : Many posts can be associated with one user. 
    # back_populates links this relationship to the 'posts' relationship in User 
    author: Mapped['User'] = relationship(back_populates='posts')

    def __repr__(self) -> str:
        return f"Post(id={self.id!r}, title={self.title!r}, user_id={self.user_id!r})"
    

# Defining a helper funciton to setup the database
def setup_orm_database(db_url: str):
    """Setting up ORM Database.""" 
    print(f"Setting up ORM Database at {db_url}...")
    # Create the database engine
    engine = create_engine(db_url, echo=True)

    # Creating Tables in the database
    try:
        # We can drop all tabls if already exists.
        Base.metadata.drop_all(engine)
        # Create all table defined in the Base.metadata 
        Base.metadata.create_all(engine)
        print("Database setup with all tables in {db_url} successfully.")
    except Exception as e:
        print(f"Error setting up database: {e}")
    finally:
        if engine:
            engine.dispose()

if __name__ == "__main__":
    # Setup the ORM Database
    setup_orm_database(DATABASE_URL)
