# Complex Data Retrieval with Joins (ORM)

The ORM makes joining tables and querying across relationships much more intuitive than with Core's expression language.

**Key concepts:**

- **`join()` and `outerjoin()`**: Methods on `select()` statements to combine rows from two or more tables based on a related column between them.

    - `join()`: Inner join, returns only rows where there is a match in both tables.

    - `outerjoin()`: Left outer join, returns all rows from the "left" table, and the matched rows from the "right" table. If no match, NULLs are returned for the right table's columns.

- **Joining on relationships**: SQLAlchemy can automatically infer join conditions when you join via a defined `relationship()`. This is often preferred.

- **Using `contains_eager()` for efficient loading of joined data**: While `join()` itself retrieves columns from both tables, `contains_eager()` tells the ORM that the columns from the _joined_ table should be eagerly loaded into the _relationship_ attribute of the primary model. This is advanced, usually for very specific performance tuning. 

    For general eager loading, `joinedload` is more common.

- **Aliasing tables in joins (`aliased()`)**: Necessary when you need to join the same table multiple times in a single query.

- **Aggregations with `func` (e.g., `count()`, `sum()`, `avg()`)**: Use the `func` object to call SQL aggregate functions.

- **Grouping data (`group_by()`) and filtering groups (`having()`)**: Standard SQL `GROUP BY` and `HAVING` clauses.

## Code Break Down

### Postgres Implementation

```python
import os
import datetime 
from typing import List, Optional 
from sqlalchemy import create_engine, ForeignKey, String, Integer, Boolean, DateTime, func 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.sql import select 
from sqlalchemy.orm import aliased # for aliasing tables in joins

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
    # Requires defining new relationships or aliasing for clarity
    # Let's modify the User model to include a manager_id for this example
    
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
```

The Python script you've provided demonstrates how to use **SQLAlchemy ORM** to perform various **JOIN operations** on a PostgreSQL database. It defines two data models, `User` and `Post`, and then uses them to show how to execute different types of joins, including INNER JOIN, LEFT OUTER JOIN, and self-joins.

Let's break down the code's functionality section by section.

---

#### 1. Database Configuration and Models

The script begins by setting up the connection to a PostgreSQL database using the `psycopg` driver. It defines a `DATABASE_URL` string with the host, port, database name, user, and password.

Python

```
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "my_sqlalchemy_db"
DB_USER = "sqlalchemy"
DB_PASSWORD = "sqlalchemy_password"
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
```

The core of the ORM functionality is defined by two classes that inherit from `DeclarativeBase`:

- **`User`**: This class maps to a `users` table. It has columns for `id`, `name`, `email`, `is_active`, and `created_at`. The `posts` relationship tells SQLAlchemy that a `User` can have many `Post` objects, and it should be managed with `back_populates` and `cascade` for automatic updates and deletions.
    
- **`Post`**: This class maps to a `posts` table. It has columns for `id`, `title`, `content`, `user_id` (a **foreign key**linking to `users.id`), and `published_at`. The `author` relationship links a `Post` to its `User` object.
    

This is a classic **one-to-many relationship**, where one user can have many posts. SQLAlchemy manages the `JOIN` logic behind the scenes because of these defined relationships.

---

#### 2. Setting Up the Data

The `setup_orm_data_for_joins(engine)` function is a crucial helper that prepares the database for the JOIN examples.

1. **Drops and Creates Tables**: It first drops any existing tables and then creates the `users` and `posts`tables based on the ORM models.
    
2. **Populates Data**: It then creates a `Session` and populates the tables with sample data. It adds four users (`Alice`, `Bob`, `Charlie`, and `David`) and four posts, with `Alice` having two posts and `Bob` and `Charlie` having one each. `David` is added to demonstrate cases where a user has no posts.
    

This setup ensures that the subsequent JOIN operations will have meaningful data to query.

---

#### 3. Performing the JOIN Operations

The `perform_orm_joins(engine)` function contains the main examples of different JOIN types. Each example creates a new `Session` and executes a specific query using SQLAlchemy's `select` function.

1. Inner Join

    - **Code**: `statement = select(User, Post).join(User.posts)`
        
    - **Explanation**: This query gets **only the users who have at least one post**. SQLAlchemy automatically infers the join condition (`posts.user_id = users.id`) from the `User.posts` relationship. The result is a list of tuples, where each tuple contains a `User` object and a `Post` object. Notice that `David` is not included in the results because he has no posts.
    

2. Left Outer Join

    - **Code**: `statement = select(User, Post).outerjoin(User.posts)`
        
    - **Explanation**: This query gets **all users**, including those without any posts. The `outerjoin` method with the relationship tells SQLAlchemy to include all users from the "left" side (`User` table) of the join, even if there's no matching record in the "right" side (`Post` table). The output for `David` shows `User: David, Post: No Post`, which demonstrates the outer join's behavior.
    

3. Join with `WHERE` Clause

    - **Code**: `statement = select(Post.title, User.name).join(Post.author).where(User.name == 'Alice')`
        
    - **Explanation**: This is a standard `INNER JOIN` with a filter. It joins the `Post` and `User` tables and then filters the results to only include posts where the author's name is `'Alice'`. This is a common way to query for specific data across multiple tables.
        

4. Aggregations with `GROUP BY`

    - **Code**: `statement = select(User.name, func.count(Post.id)).outerjoin(User.posts).group_by(User.name)`
        
    - **Explanation**: This query calculates the number of posts for each user.
        
        - It uses an `OUTER JOIN` to ensure that users with zero posts are also included in the count.
            
        - The `func.count(Post.id)` aggregates the posts.
            
        - The `.group_by(User.name)` clause groups the results by user, so the count is performed for each individual user. The output correctly shows that `David` has a count of 0.
            

5. Aggregations with `HAVING` Clause

    - **Code**: `statement = select(User.name, post_count_alias).join(User.posts).group_by(User.name).having(post_count_alias > 1)`
        
    - **Explanation**: This query is similar to the `GROUP BY` example, but it adds a `HAVING` clause.
        
        - A `HAVING` clause is used to filter aggregated results.
            
        - The query first groups the users and counts their posts.
            
        - The `.having(post_count_alias > 1)` then filters these groups, keeping only the users who have more than one post. In this case, only `Alice` will be returned.
        

6. Self-Join

    - **Code**: `alice = aliased(User); OtherUser = aliased(User); ... join(alice, ...)`
        
    - **Explanation**: A **self-join** is when a table is joined to itself. This is useful for finding relationships within the same table, such as finding users who were created on the same day.
        
        - To do this, you must **alias** the table twice (`alice` and `OtherUser`) to treat them as two separate entities in the query.
            
        - The query joins the `User` table to itself (`join(alice, ...)`).
            
        - The join condition (`func.date(OtherUser.created_at) == func.date(alice.created_at)`) compares the creation dates of the users.
            
        - The `where` clauses (`where(alice.name == 'Alice')` and `where(OtherUser.name != 'Alice')`) filter the results to find other users who were created on the same day as Alice but are not Alice herself.

### SQLite Implementation

```python
import os
import datetime 
from typing import List, Optional 
from sqlalchemy import create_engine, ForeignKey, String, Integer, Boolean, DateTime, func 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.sql import select 
from sqlalchemy.orm import aliased # for aliasing tables in joins

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
    # Requires defining new relationships or aliasing for clarity
    # Let's modify the User model to include a manager_id for this example
    
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
```

### Key Changes

1. **Database Connection**: The PostgreSQL-specific connection parameters (`DB_HOST`, `DB_PORT`, etc.) have been removed and replaced with a single `DATABASE_URL` for SQLite:
    
    unfold_lesspython
    
    content_copyadd
    
    `DATABASE_URL = "sqlite:///my_joins_db.db"`
    
    This tells SQLAlchemy to create and use a database file named `my_joins_db.db` in the same directory.
    
2. **No Other Code Changes**: That's it! The ORM models (`User`, `Post`) and all the join queries (`INNER JOIN`, `LEFT OUTER JOIN`, `GROUP BY`, `HAVING`, and the `SELF JOIN`) are written in a way that is independent of the specific SQL dialect. SQLAlchemy handles the translation to the correct syntax for SQLite automatically.

