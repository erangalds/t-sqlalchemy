# Defining Models (Using Declarative Base)

Defining models with Declarative Base involes creating python classes that inherit from Base (created by declarative_base()). 

## Key Elements

+ `__tablename__`: A required class attribute that specifies the name of the table this class maps to.

+ `column`: Used to define individual columns, similar to SQLAlchemy Core. 

+ `Mapped`: A type annotation used in SQLAlchemy 2.0+ to indicate that an attribute is mapped to a database column. It's used in conjunction with `mapped_column()`.

+ `mapped_column()`: The function used to define a mapped column. It wraps the `Column` object with ORM specific functionality. 

+ **Primary Keys and Autoincrementing IDs**: Defined using `primary_key=True` and `autoincrement=True`.

+ **Basic column types and their mapping**: Similar to Core (e.g. Integer, String, Boolean, DateTime, etc)



Those are the simple concepts we need to know. So now let me show how to put this into action. Let's look at a small example. 


---

## Code Breakdown
### Postgres Implementaton 

```python
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
    # One-to-Many Relationshihp : A User can publish Many Posts
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

```

#### **Database Connection** 🔗

The script starts by defining the connection parameters for a **PostgreSQL database**, including the host, port, name, user, and password. It then constructs a **`DATABASE_URL`** string in the format required by SQLAlchemy's `psycopg` dialect (which is used to connect to PostgreSQL). This connection string is essential for SQLAlchemy to know how to communicate with the database.

#### **Declarative Base Class** 📝

The **`Base`** class, which inherits from `DeclarativeBase`, acts as the foundation for all the ORM models. Any class that inherits from `Base` is a declarative model, and SQLAlchemy will use it to map Python objects to database tables. This is a core part of SQLAlchemy's modern ORM approach.

#### **ORM Models** 🧩

Then I define two classes, **`User`** and **`Post`**, which are the ORM models. Each class inherits from `Base` and represents a table in the database.

- **`User` Model:** This model maps to the **`users`** table.
    
    - It defines columns such as **`id`** (a primary key that auto-increments), **`name`**, **`email`** (which is unique), **`is_active`**, and **`created_at`**.
        
    - The **`posts`** field is a **relationship**. This line tells SQLAlchemy that a `User` object can have multiple associated `Post` objects. The `back_populates` argument creates a bidirectional relationship with the `Post`model's `author` field.
        
    - The `cascade="all, delete-orphan"` ensures that when a user is deleted from the database, all their associated posts are also deleted. This is a crucial feature for maintaining data integrity.
        
- **`Post` Model:** This model maps to the **`posts`** table.
    
    - It defines columns for **`id`** (primary key), **`title`**, **`content`**, and **`published_at`**.
        
    - The **`user_id`** column is a **foreign key** that links each post to a user. It references the **`id`** column of the **`users`** table.
        
    - The **`author`** field is a **relationship**. This indicates that each `Post` object is associated with a single `User`object. The `back_populates='posts'` links this relationship back to the `posts` field in the `User` model, completing the bidirectional link.
        
    - This is an example of a **one-to-many relationship**: one user can have many posts, but each post belongs to only one user.
        

---

#### **Database Setup Function** 🛠️

The **`setup_orm_database`** function is a utility for creating and managing the database schema.

- It creates a **`create_engine`** object, which is the central point of contact for the database.
    
- The `echo=True` argument makes SQLAlchemy print all the SQL commands it generates, which is very helpful for debugging.
    
- Inside the function, it first calls **`Base.metadata.drop_all(engine)`** to remove any existing tables, ensuring a clean slate.
    
- It then calls **`Base.metadata.create_all(engine)`** to create the tables defined by the `User` and `Post` models. This is where SQLAlchemy translates the Python classes into SQL `CREATE TABLE` statements.
    
- Finally, the engine is disposed of to release the database connection resources.
    

---


#### **Understanding `back_populates`** 🔄

`back_populates` in SQLAlchemy ORM allows you to define a **bidirectional relationship** between two models. It ensures that when you modify one side of the relationship, the other side is automatically updated to maintain consistency.

In our code, `back_populates` is used to link the `posts` relationship in the `User` model with the `author` relationship in the `Post` model.

- **Without `back_populates`**: If we only define `posts` in `User` and `author` in `Post` without `back_populates`, SQLAlchemy would manage them as two separate, independent relationships. When we add a `Post` to a `User`'s `posts` list, the `user_id` on the `Post` object wouldn't automatically be set, nor would the `author` attribute on the `Post` object be linked back to the `User`. We'd have to manage both sides manually.
    
- **With `back_populates`**: When `back_populates` is used, SQLAlchemy understands that these two `relationship()` declarations are **two halves of the same whole**.
    
    - If we append a `Post` object to `user.posts`, SQLAlchemy automatically sets the `post.user_id` to `user.id`and also sets `post.author` to `user`.
        
    - Conversely, if we set `post.author = user`, SQLAlchemy automatically adds `post` to `user.posts`.
        

This bidirectional linking is crucial for **data integrity** and makes working with related objects much more intuitive and less error-prone. It's like having two doors to the same room; opening one automatically affects the other, keeping them in sync.

#### **How the Relationship is Defined** 🤝

The relationship between `User` and `Post` is a **One-to-Many** relationship, meaning one `User` can have many `Posts`, but each `Post` belongs to only one `User`.

Let's break down how this is established in your code:

1. **Foreign Key (Many Side - `Post` Table)**:
    
    ```python
    class Post(Base):
        # ...
        user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
        # ...
    ```
    
    - The `user_id` column in the `Post` model is defined as an `Integer`.
        
    - `ForeignKey("users.id")` is the critical part here. It explicitly tells SQLAlchemy that this `user_id`column in the `posts` table refers to the `id` column in the `users` table. This is how the database enforces the link between a post and its author.
        
    - `nullable=False` means that every `Post` _must_ have an associated `User`.
        
2. **Relationship on the "Many" Side (`Post` Model)**:
    
    ```python
    class Post(Base):
        # ...
        author: Mapped['User'] = relationship(back_populates='posts')
        # ...
    ```
    
    - `author: Mapped['User']`: This line defines an attribute `author` on the `Post` model. When you access `post.author`, SQLAlchemy will fetch the associated `User` object.
        
    - `relationship(back_populates='posts')`: This tells SQLAlchemy that this `author` relationship is the "other side" of the `posts` relationship defined in the `User` model. It points back to the collection of posts on the `User` object.
        
3. **Relationship on the "One" Side (`User` Model)**:
    
    ```python
    class User(Base):
        # ...
        posts: Mapped[List["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")
        # ...
    ```
    
    - `posts: Mapped[List["Post"]]`: This defines an attribute `posts` on the `User` model. When you access `user.posts`, SQLAlchemy will return a list of all `Post` objects associated with that `User`. The `List` type hint indicates that it's a collection.
        
    - `relationship(back_populates="author", ...)`: This tells SQLAlchemy that this `posts` relationship is the "other side" of the `author` relationship defined in the `Post` model.
        
    - `cascade="all, delete-orphan"`: This is an important **cascading behavior** setting:
        
        - `all`: This implies `save-update` and `delete` cascade. If you save a `User` object, any new `Post` objects added to `user.posts` will also be saved. If you delete a `User` object, all associated `Post` objects will also be deleted from the database.
            
        - `delete-orphan`: This is specifically for collections. If a `Post` object is removed from the `user.posts` list (i.e., it's "orphaned" from its parent `User` without being assigned to another `User`), it will be deleted from the database.

### SQLite Implementation

```python
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
```

### **Changes Required** 🛠️

1. **Remove PostgreSQL-specific connection parameters.** The variables `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` are not needed for SQLite as it operates on a file-based database.
    
2. **Update the `DATABASE_URL`.** The new URL will specify the SQLite dialect and the path to the database file. For a file named `blog.db`, the URL will be `"sqlite:///blog.db"`. The three slashes `///` indicate that the database file is located in the current directory. If you wanted the file to be in memory, you'd use `"sqlite:///:memory:"`.




