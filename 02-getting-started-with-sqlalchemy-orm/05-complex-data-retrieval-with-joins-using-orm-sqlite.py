import os
import datetime 
from typing import List, Optional 
from sqlalchemy import create_engine, ForeignKey, String, Integer, Boolean, DateTime, func 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.sql import select 
from sqlalchemy.orm import aliased # for aliasing tables in joins

## Configuration for Database Connection 
# SQLite uses a file-based database.
DATABASE_URL = "sqlite:///my_joins_db.db"

# Defining the Declarative Base Class
class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models.""" 
    pass

## Defining ORM Models
class User(Base):
    """ORM Model for User Table."""
    __tablename__ = "users" # Mapping to the 'users' table 
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    posts: Mapped[List['Post']] = relationship(
        back_populates='author',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'User(id={self.id!r}, name={self.name!r}, email={self.email!r})'
    
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
    
# Defining Helper function to seup and populate data ---
def setup_orm_data_for_joins(engine):
    """Setting up the Data for the Database Tables"""
    print(f'\n#-------------------------------- Setting Up Tables -----------------------------#\n')
    # Dropping the tables if required
    Base.metadata.drop_all(engine)
    # Creating the tables
    Base.metadata.create_all(engine)
    print(f'Database Tables created successfully')

    # Starting to Enter data
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)
    with Session() as session:
        # Create Users
        user_alice = User(name='Alice', email='alice@example.com')
        user_bob = User(name='Bob', email='bob@example.com')
        user_charlie = User(name='Charlie', email='charlie@example.com')
        user_david = User(name='David', email='david@example.com')

        session.add_all([user_alice, user_bob, user_charlie, user_david]) # Marking User Data Records to add
        session.commit() # Committing the changes

        # Create Posts
        post_alice_1 = Post(title='Alice\'s First Post', content='This is content of Alice\'s first post.', author=user_alice)
        post_alice_2 = Post(title='Alice\'s Second Post', content='This is content of Alice\'s second post.', author=user_alice)
        post_bob_1 = Post(title='Bob\'s First Post', content='This is content of Bob\'s first post.', author=user_bob)
        post_charlie_1 = Post(title='Charlie\'s First Post', content='This is content of Charlie\'s first post.', author=user_charlie)
        
        session.add_all([post_alice_1, post_alice_2, post_bob_1, post_charlie_1]) # Marking Post Data Records to add
        session.commit() # Commiting Changes

        print(f'Initial Data Populated for JOIN Examples....')

# Performing JOIN Operations
def perform_orm_joins(engine):
    """Performing JOIN Operations"""
    print(f'#\n---------------------------- JOIN Operations -----------------------------#\n')

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)

    # 1. INNER JOINS : Get Users and Their Posts
    print(f'\n----------------------------- INNER JOIN -----------------------------------\n')
    with Session() as session:
        # Joining on relationship. SQLAlchemy infers posts.user_id == users.id
        statement = select(User, Post).join(User.posts).order_by(User.name, Post.title)
        results = session.execute(statement).all()

        for user, post in results:
            print(f'User: {user.name}, Post: {post.title}')
    
    # 2. Left Outer Join: Get all Users, and their Posts if they have any
    print(f'\n----------------------------- LEFT OUTER JOIN ---------------------------------\n')
    with Session() as session:
        # Joining on relationship with isouter=True for outer join
        statement = select(User, Post).outerjoin(User.posts).order_by(User.name, Post.title)
        results = session.execute(statement).all()

        for user, post in results:
            print(f'User: {user.name}, Post: {post.title if post else "No Post"}')

    # 3. JOIN with Filtering using WHERE Clause
    print(f'\n------------------------------- JOIN with WHERE -------------------------------\n')
    with Session() as session:
        # We can filter eihter table
        statement = select(Post.title, User.name).join(Post.author).where(User.name == 'Alice')
        results = session.execute(statement).all()

        for post_title, author_name in results:
            print(f'Post Title: {post_title}, Author: {author_name}')
    
    # 4. Aggregations (e.g. Count of Posts per User) with GROUP BY
    print(f'\n--------------------------------- Aggregations ---------------------------------\n')
    print(f'\n--------------------------------- Group BY ---------------------------------\n')
    with Session() as session:
        statement = select(User.name, func.count(Post.id).label("post_count")) \
            .outerjoin(User.posts) \
            .group_by(User.name) \
            .order_by(User.name)
        
        results = session.execute(statement).all()

        for user_name, post_count in results:
            print(f'User: {user_name}, Post Count: {post_count}')

        
    # 5. Aggregations with HAVING Clause
    print(f'\n--------------------------------- HAVING Clause ---------------------------------\n')
    with Session() as session:
        post_count_alias = func.count(Post.id).label('post_count')
        statement = select(User.name, post_count_alias) \
            .join(User.posts) \
            .group_by(User.name) \
            .having(post_count_alias > 1) \
            .order_by(User.name)
        
        results = session.execute(statement).all()

        for user_name, post_count in results:
            print(f'User: {user_name}, Post Count: {post_count}')

    # 6. JOINNING the Same Table (Self JOIN)
    print(f'\n---------------------------------- SELF JOIN -----------------------------------\n')
    # Example 1: Finding users created on the same day as Alice
    with Session() as session:
        alice = aliased(User) # Alias the User table to represent Alice
        OtherUser = aliased(User) # Alias the User table to represent other users

        # We use func.date() to compare only the date part of the created_at timestamp,
        # ignoring the time. This is because each user will have a slightly different timestamp.
        statement = select(OtherUser.name, alice.name) \
            .join(alice, func.date(OtherUser.created_at) == func.date(alice.created_at)) \
            .where(alice.name == 'Alice') \
            .where(OtherUser.name != 'Alice')
        results = session.execute(statement).all()

        if results:
            for other_name, alice_name in results:
                print(f'{other_name} was created on the same day as {alice_name}')
        else:
            print(f'No other users were found created on the same day as Alice')

    
# Main Execution Block
if __name__ == "__main__":
    # Create the database engine
    engine = create_engine(DATABASE_URL, echo=True)
    # Setup Tables
    setup_orm_data_for_joins(engine)
    # Perform JOIN Operations
    perform_orm_joins(engine)
    # Dispose the engine
    engine.dispose()
