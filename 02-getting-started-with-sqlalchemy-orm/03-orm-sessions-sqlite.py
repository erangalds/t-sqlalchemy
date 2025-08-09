import os
import datetime 
from typing import List, Optional
from sqlalchemy import create_engine, ForeignKey, String, Integer, Boolean, DateTime 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker 
from sqlalchemy.exc import IntegrityError, NoResultFound, MultipleResultsFound 
from sqlalchemy.sql import select

## Configuration for Database Connection 
# Create a file-based SQLite database connection string.
# The database will be created in the same directory as the script.
DATABASE_URL = "sqlite:///my_database.db"

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
    
# Helper function to setup and get Session Factory
def get_session_factory(db_url: str, echo: bool = True) -> sessionmaker:
    """Create a session factory for the database."""
    print(f'Setting up the ORM for database: {db_url}')
    # Create the database engine
    engine = create_engine(db_url, echo=echo)
    # Drop the tables in the database
    Base.metadata.drop_all(engine)
    # Create the tabale in the database
    Base.metadata.create_all(engine)
    print(f'Database Tables created successfully.')
    
    return sessionmaker(autocommit=False, autoflush=False,bind=engine, expire_on_commit=True)

# Defining the CRUD operations
def perform_orm_crud_operations(Session: sessionmaker): 
    """Perform CRUD operations using SQLAlchemy ORM."""
    #---------------------------------- CREATE (Add Objects)-----------------------"""
    with Session() as session: # Using the context manager to handle the session
        print(f'\n---------------------Creating Users and Posts-------------------------\n')
        # Defining Users
        user1 = User(name="Alice", email='alice@example.com')
        user2 = User(name="Bob", email='bob@example.com', is_active=True)
        user3 = User(name="Charlie", email='charlie@example.com')

        # Defining Posts
        post1 = Post(title='Alice\'s First Post', content='This is Alice\'s first post.', author=user1)
        post2 = Post(title='Bob\'s First Post', content='This is Bob\'s first post', author=user2)
        post3 = Post(title='Charlie\'s First Post', content='This is Charlie\'s first post.', author=user3)
        
        # Adding the users to the session
        session.add_all([user1, user2, user3]) # Add multiple users
        session.commit() # Commit the changes
        print('Users added successfully.')

        # Adding posts for the users
        # Adding the posts to the session
        session.add_all([post1, post2, post3])
        session.commit()
        print('Posts added successfully.')


    # READ Operation
    with Session() as session: # Using the context manager to handle the session
        # Get all users
        print(f'\n---------------------Retrieving all users-------------------------\n')
        users = session.execute(
            select(User).order_by(User.name)
        ).scalars().all()

        # Printing Users
        for user in users:
            print(user)

        # Get a User with Specific UserID
        print(f'\nRetrieving User: Alice\n')
        user_alice = session.execute(
            select(User).where(User.name == 'Alice')
        ).scalar_one()

        print(f'User: {user_alice}')

        # Querying for active_users
        print(f"\n---------------------Active User:--------------------------------\n")
        active_users = session.execute(
            select(User).where(User.is_active == True)
        ).scalars().all()

        for user in active_users:
            print(f'User ID: {user.id}, Name: {user.name}')
        

        # Query Posts with Filtering
        print(f'\n#--------------------Posts by Alice------------------------------#\n')
        alice_posts = session.execute(
            select(Post).where(Post.author == user_alice).order_by(Post.published_at)
        ).scalars().all()

        for post in alice_posts:
            print(f'Post ID: {post.id}, Title: {post.title}, Author: {post.user_id}')

        # Demonstrating lazy loading
        # Each access to user.posts will cause a separate query if not loaded
        print(f'\n\nAccessing Posts via user.posts (lazy loading):\n')
        for user in users:
            print(f'User: {user.name}')
            for post in user.posts:
                print(f'  Post: {post.title}')
        

    # Update (Modify Objects)
    print(f'\n#--------------------------Update Objects-----------------------------\n')
    with Session() as session:
        # Retrieve the user to update
        print(f'Updating User: Bob\n')
        bob = session.execute(
            select(User).where(User.name == 'Bob')
        ).scalar_one() 

        if bob: 
            print(f'Current Name: {bob.name}')
            # Changing the name
            bob.name = "Robert"
            session.add(bob) # Mark the object
            session.commit() # Commit the changes
            print(f'Updated Name: {bob.name}')

        # Update a Post
        print(f'\nUpdating Post Content By: Alice\n')
        alice_post = session.execute(
            select(Post).where(Post.title == 'Alice\'s First Post')
        ).scalar_one()
        
        if alice_post:
            print(f'Current Content: {alice_post.content}')
            # Changing the Cotent
            alice_post.content = "Updated content for Alice's first post."
            session.add(alice_post)
            session.commit()
            print(f'Updated Content: {alice_post.content}')

        # Deactivate Charlie
        print(f'\nDeactivating User: Charlie\n')
        charlie = session.execute(
            select(User).where(User.name == 'Charlie')
        ).scalar_one()

        if charlie:
            print(f'Current Status: {charlie.is_active}')
            # Deactivate Charlie
            charlie.is_active = False
            session.add(charlie)
            session.commit()
            print(f'Updated Status: {charlie.is_active}')

    # Verify Updates
    with Session() as session: 
        print(f'\n#-------------------------Verify Updates----------------------------#\n')
        # Updated User
        updated_bob = session.execute(
            select(User).where(User.email == 'bob@example.com')
        ).scalar_one()

        print(f'Updated Bob\'s Name: {updated_bob.name}\n')

        # Updated Post
        updated_post = session.execute(
            select(Post).where(Post.title == 'Alice\'s First Post')
        ).scalar_one()

        print(f'Updated Post Content: {updated_post.content}\n')
        
        # Deactivated Charlie
        updated_charlie = session.execute(
            select(User).where(User.name == 'Charlie')
        ).scalar_one()

        print(f'Charlie\'s Status : {updated_charlie.is_active}\n')

    
    # DELETE Operations
    print(f'\n#--------------------------------Delete Objects----------------------------\n')
    with Session() as session: 
        # Retrieve an Object to Delete
        user_to_delete = session.execute(
            select(User).where(User.name == 'Charlie')
        ).scalar_one()

        if user_to_delete: 
            session.delete(user_to_delete) # Mark the Object for Deletion
            session.commit() # Commit the deletion
            print(f'Deleted User: Charlie\n')

        # Verify deletion
        remaining_users = session.execute(
            select(User)
        ).scalars().all()

        print(f'\nRemaining Users:')
        for user in remaining_users:
            print(f'User ID: {user.id}, Name: {user.name}')
        
        # Remaining Posts
        remaining_posts = session.execute(
            select(Post)
        ).scalars().all()

        print(f'\nRemaining Post:')
        for post in remaining_posts:
            print(f'Post ID: {post.id}, Title: {post.title}, Authos: {post.user_id}')
        
    print(f"END of ORM CRUD Operations")

# Main Execution Block
if __name__ == "__main__":
    # Get Session
    session_factory = get_session_factory(DATABASE_URL, echo=False)
    # Perform CRUD Operations
    perform_orm_crud_operations(session_factory)