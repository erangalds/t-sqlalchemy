# ORM Sessions

The `Session` object is the central component for interacting with the databasae when using SQLAlchemy ORM. It's a key abstraction that manages the lifecycle of your ORM objects and database transactions. 

## Understanding the `Session` Object and its role in ORM:

+ **Unit of Work**: The `Session` maintains a *Unit of Work*, which is a collection of objects that we have loaded, created, modified, or marked for deletion. It tracks changes to these objects. 

+ **Transaction Management**: Each `Session` operates within a database transaction. Changes are not commited to the database until `session.commit()` is called. If an error occurs, `session.rollback()` can revert all changes in that transaction. 

+ **Object Identity Map**: The `Session` maintains an identity map, ensuring that for a given primary key, only one python object instance exists within that session. This prevents inconsistencies when fetching the same data multiple times. 

+ **Lady Loading**: By default, relationshiphs are "lazy loaded". When you access a related object (e.g. `user.posts`), SQLAlchemy will issue a separate query to load that data only when it's accessed. 

### `sessionmaker()`: 

`sessionmaker()` is a factory function that creates a `Session` class. You configure this `Session` class with an `Engine`. Each call to the created `Session` class will then return a new, independent `Session` object. 

### Key `Session` methods:

+ `session.add()`: Adds a new, transient object (an object not yet associated with a session or database now) to the session. 

+ `session.add_all()`: Adds a list of objects to the session. 

+ `session.commit()`: Commits the current transaction, flushing all pending changes (inserts, updates, deletes) from the session to the database and then commiting the transaction. 

+ `session.rollback()`: Rolls back the current transaction, discarding all uncommitted changes in the session and reverting the database to its state before the transaction began. 

+ **`session.refresh()`**: Reloads the state of an object from the database, discarding any changes made in the session. Useful for refreshing an object after another session might have updated it.

+ **`session.expunge()`**: Detaches an object from the session. The object becomes "detached" and can no longer participate in the session's unit of work.

+  **`session.close()`**: Closes the session, releasing its database connection. It's crucial to close sessions to return connections to the pool. Using a context manager (`with Session() as session:`) is the recommended way to ensure sessions are always closed.

## Unit of Work Patter: 

The `Session` encapsulates the Unit of Work pattern. Instead of executing an `INSERT`statement for every `session.add()` call immediately, the `Session` tracks all changes (objects added, modified, or deleted). When `session.commit()` is called, SQLAlchemy intelligently groups these changes, flushes them to the database in the correct order (e.g., inserting parent records before child records), and then commits the database transaction. This makes operations more efficient and ensures data integrity. 

Now let me show you how this works using a simple example. 

## Code Break Down - 

### Postgres Implementation

```python
import os
import datetime 
from typing import List, Optional
from sqlalchemy import create_engine, ForeignKey, String, Integer, Boolean, DateTime 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker 
from sqlalchemy.exc import IntegrityError, NoResultFound, MultipleResultsFound 
from sqlalchemy.sql import select

## Configuration for Database Connection 
# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "my_sqlalchemy_db"
DB_USER = "sqlalchemy"
DB_PASSWORD = "sqlalchemy_password"

# Create connection string (using psycopg3)
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

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
def get_session_factory(db_url: str, db_name: str, echo: bool = True) -> sessionmaker:
    """Create a session factory for the database."""
    print(f'Setting up the ORM for database: {db_name}')
    # Create the database engine
    engine = create_engine(db_url, echo=echo)
    # Delete the current tables if they exists
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
    session_factory = get_session_factory(DATABASE_URL, DB_NAME, echo=False)
    # Perform CRUD Operations
    perform_orm_crud_operations(session_factory) 
    
```
---

#### 1. Database Configuration and Connection

The script begins by setting up the database connection parameters for a **PostgreSQL database**. It defines constants for the host, port, name, user, and password. These are then used to construct a `DATABASE_URL` string in the standard format `postgresql+psycopg://user:password@host:port/database`. The `psycopg` part indicates that the `psycopg` driver (version 3) will be used to connect to the PostgreSQL database.

#### 2. ORM Model Definition

This section defines the database schema using **SQLAlchemy's ORM** (Object-Relational Mapping).

- **`Base` Class:** A `DeclarativeBase` class is created, which serves as the foundation for all the ORM models. All model classes must inherit from this `Base` class.
    
- **`User` Model:** This class maps to a `users` table.
    
    - It defines columns like `id`, `name`, `email`, `is_active`, and `created_at`.
        
    - `Mapped[]` and `mapped_column()` are used to define the column types and properties.
        
    - `primary_key=True`, `autoincrement=True`, and `unique=True` are used to set constraints.
        
    - The `posts` attribute is a `relationship` that links a user to their posts. The `back_populates` argument ensures a bidirectional relationship, and `cascade='all, delete-orphan'` means that if a user is deleted, all of their associated posts will also be deleted.
        
- **`Post` Model:** This class maps to a `posts` table.
    
    - It includes columns for `id`, `title`, `content`, and `published_at`.
        
    - The `user_id` column is defined as a `ForeignKey`, linking each post to a user in the `users` table.
        
    - The `author` attribute is a `relationship` that links each post back to its `User` object.
        

---

#### 3. Session and CRUD Operations

- **`get_session_factory` Function:** This helper function sets up the database **engine** and **session factory**.
    
    - It creates the `engine` which manages the database connection pool.
        
    - `Base.metadata.drop_all(engine)` and `Base.metadata.create_all(engine)` are called to drop all existing tables and then create new ones based on the defined models (`User` and `Post`). This is useful for testing or a clean setup.
        
    - Finally, it returns a `sessionmaker` object, which is a factory for creating new `Session` objects.
        
- **`perform_orm_crud_operations` Function:** This is the core of the script, where all the database interactions happen. It uses a `with Session() as session:` block to ensure proper session management and automatically commit or rollback transactions.
    

**Create**

- New `User` and `Post` objects are instantiated.
    
- `session.add_all()` is used to stage multiple objects for insertion.
    
- `session.commit()` persists the changes to the database.
    

**Read**

- `session.execute(select(Model))` is used to construct and execute queries.
    
- `scalars().all()` retrieves all the results as a list of ORM objects.
    
- `scalar_one()` is used to retrieve a single object, raising an exception if no or multiple results are found.
    
- The code demonstrates querying for all users, a specific user by name, active users, and posts by a specific user.
    
- It also shows how to access related objects through the `relationship` attribute (e.g., `user.posts`), which uses **lazy loading** to fetch related data only when it's accessed.
    

**Update**

- An object is first retrieved from the database.
    
- Its attributes are then directly modified (e.g., `bob.name = "Robert"`).
    
- `session.add(bob)` is called to mark the object as modified (though SQLAlchemy often detects this automatically).
    
- `session.commit()` saves the changes to the database.
    

**Delete**

- An object to be deleted is retrieved from the database.
    
- `session.delete()` marks the object for deletion.
    
- `session.commit()` executes the deletion.
    
- Because of the `cascade='all, delete-orphan'` setting on the `User` model's `posts` relationship, when a `User`is deleted, their associated `Post` objects are also automatically deleted.

### SQLite Implemetation 

```python

```

#### Database Connection and Setup

- **PostgreSQL Script:** Uses a detailed connection string with specific parameters like `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`. The connection string format `postgresql+psycopg://...` specifies the database type and the driver to use. It also includes a `Base.metadata.drop_all(engine)` call to clear the database tables before recreating them.
    
- **SQLite Script:** Uses a much simpler connection string: `sqlite:///my_database.db`. This is creates a SQLite database instance persisted to a file named `my_database.db`, within the same directory. The reamining parts are exactly the same. This also uses `Base.metadata.drop_all(engine)` to clear the database and `Base.metadata.create_all(engine)` to create all the tables. 

