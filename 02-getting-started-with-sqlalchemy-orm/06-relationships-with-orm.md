# Relationships with SQLAlchemy ORM

Relationships are the heart of ORM, allowing you to connect Python objects in a natural, object-oriented way, mirroring the foreign key relationships in your database.

I briefly touched upon this in defining models. Now let's explore them in more detail.

## Types of Relationships

- **One-to-Many Relationships (`relationship()` and `ForeignKey`)**:

    - The "one" side (e.g., `User`) has a collection of "many" related objects (e.g., `Post`s).

    - Defined on the "one" side using `relationship()` with `back_populates`.

    - The "many" side (e.g., `Post`) typically holds the `ForeignKey` column pointing back to the "one" side.

- **Many-to-One Relationships**:

    - The "many" side (e.g., `Post`) refers to a single "one" related object (e.g., `User`).

    - Defined on the "many" side using `relationship()` with `back_populates`.

    - The `ForeignKey` is typically on this "many" side.

- **Many-to-Many Relationships**:
    - When records in one table can relate to multiple records in another table, and vice versa (e.g., `Student`s can enroll in many `Course`s, and `Course`s can have many `Student`s).

    - Requires an **association table** (or join table) in the database to link the two main tables. This table typically has two foreign keys, one to each of the primary tables.

    - The `relationship()` definition uses `secondary` to point to this association table.
    

## Loading Strategies

When you query an ORM object, its related objects (via `relationship()`) are not necessarily loaded from the database immediately. SQLAlchemy provides several loading strategies to control when and how related data is fetched. This is crucial for performance (avoiding the N+1 problem).

- **Lazy Loading (Default)**:

    - Related objects are loaded **only when they are first accessed**.

    - **Pros:** Only fetches data that is actually needed, saving memory and initial query time.

    - **Cons:** Can lead to the "N+1 query problem" (one query for the main objects, then N additional queries for 
    their related objects, where N is the number of main objects). This can be a major performance bottleneck.

- **Eager Loading**: Fetches related objects as part of the _initial query_ that loads the main objects.
    - **`joinedload()`**: Performs an `OUTER JOIN` to load related data. Good for one-to-one or many-to-one relationships, or when you expect all parents to have children.

    - **`subqueryload()`**: Issues a second `SELECT` query in a subquery to fetch related data for all main objects loaded. More efficient than `joinedload` for one-to-many relationships when the "many" side can have a very large number of rows, as it avoids Cartesian product issues.

    - **`selectinload()`**: (Recommended for one-to-many/many-to-many in most cases) Issues a second `SELECT`query using `IN` clauses to fetch related data. Very efficient for collections as it queries all related objects for a given list of parent primary keys in one go, avoiding the N+1 problem without the `joinedload` Cartesian product issues.

- **`raiseload()`**: Raises an error if a lazy load is attempted. Useful for debugging N+1 problems or enforcing explicit loading strategies.

- **`noload()`**: Disables loading of the relationship entirely.


## `back_populates` and `cascade`

- **`back_populates`**: Ensures bidirectional linking. If you set `post.author = user`, `user.posts` will automatically be updated to include that post (and vice-versa). This keeps your Python objects consistent.

- **`cascade`**: Controls how operations (save, delete, refresh, merge) propagate from a parent object to its related children.
    - `"all"`: Includes `save-update`, `merge`, `refresh-expire`, `expunge`, and `delete`.

    - `"delete"`: When the parent object is deleted, the child objects are also deleted. This relies on foreign key constraints with `ON DELETE CASCADE` in the database.

    - `"delete-orphan"`: If a child object is disassociated from its parent (e.g., `user.posts.remove(post)`), it's treated as an "orphan" and marked for deletion. Requires the relationship to be non-nullable on the foreign key side.

    - `"all, delete-orphan"`: A common and powerful combination.

## Code Breakdown - Postgres Implementation

```python
import os
import datetime 
from typing import List, Optional 
from sqlalchemy import create_engine, ForeignKey, String, Integer, Boolean, DateTime, Table, Column 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker 
from sqlalchemy.sql import select 
from sqlalchemy.orm import joinedload, subqueryload, selectinload # Eager loading Strategies

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

# Association Table for Many to Many 
# This is a core table definition, no an ORM Model
# It explicitly defines the intermediate table for the many-to-many relationship
post_tags_association = Table(
    "post_tags",
    Base.metadata, # Associate with the same metadata as ORM models
    Column("post_id", ForeignKey('posts.id'), primary_key=True),
    Column("tag_id", ForeignKey('tags.id'), primary_key=True),
)

# Defining ORM Models
class User(Base):
    """ORM Model for User Table"""
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # One-to-Many relationship with Post
    posts: Mapped[List['Post']] = relationship(back_populates='author', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'User(id={self.id!r}, name={self.name!r}, email={self.email!r})'
    
class Post(Base):
    """ORM Model for Post Table"""
    __tablename__ = 'posts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))

    # Many-to-One relationship with User
    author: Mapped[Optional['User']] = relationship(back_populates='posts')

    # Many-to-Many relationship with Tag
    tags: Mapped[List['Tag']] = relationship(secondary=post_tags_association, back_populates='posts')

    def __repr__(self) -> str:
        return f'Post(id={self.id!r}, title={self.title!r})'
    
class Tag(Base):
    """ORM Model for Tag Table"""
    __tablename__ = 'tags'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    
    # Many-to-May relationship with Post
    posts: Mapped[List['Post']] = relationship(secondary=post_tags_association, back_populates='tags')

    def __repr__(self) -> str:
        return f'Tag(id={self.id!r}, name={self.name!r})'    
    

# Helper function to setup and populate data
def setup_orm_data_for_relationships(engine):
    """Setting up the Data Tables with Data"""
    print(f'\n#------------------------------- ℹ️ Setting Up Tables with data ---------------------------------#\n')
    # Dropping all tables if exists
    Base.metadata.drop_all(engine)
    # Creating all tables 
    Base.metadata.create_all(engine)    
    print(f'✅ Database Tables Creted Successfully')

    # Setting up a Session
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)

    with Session() as session:
        # Create Users
        user1 = User(name="Alice", email="alice@example.com")
        user2 = User(name="Bob", email="bob@example.com")
        session.add_all([user1, user2])
        session.commit()

        # Create posts and assign to users
        # Note: We can create posts and assign author directly
        post1 = Post(title="Alice's First Post", content="Content for A1", author=user1)
        post2 = Post(title="Bob's Important Post", content="Content for B1", author=user2)
        post3 = Post(title="Alice's Second Post", content="Content for A2", author=user1)
        post4 = Post(title="Standalone Post", content="No author yet") # Will have user_id=None
        session.add_all([post1, post2, post3, post4])
        session.commit()

        # Create tags
        tag_python = Tag(name="Python")
        tag_sqlalchemy = Tag(name="SQLAlchemy")
        tag_webdev = Tag(name="WebDev")
        session.add_all([tag_python, tag_sqlalchemy, tag_webdev])
        session.commit()

        # Associate posts with tags (Many-to-Many)
        # post1 (Alice's First Post) will have Python and SQLAlchemy tags
        post1.tags.append(tag_python)
        post1.tags.append(tag_sqlalchemy)
        # post2 (Bob's Important Post) will have Python and WebDev tags
        post2.tags.append(tag_python)
        post2.tags.append(tag_webdev)
        # post3 (Alice's Second Post) will have SQLAlchemy tag
        post3.tags.append(tag_sqlalchemy)

        session.commit()
        print(f'✅ Initial Data Populated for Relationships Examples.....')

# Perform Relationship and Loading Strategy Examples
def perform_relationship_operations(engine):
    """Performing Relationship and Loading Strategy Examples"""
    print(f'\n#-------------------------- ℹ️ Relationship Operations and Loading Strategies -------------------------#\n')

    # 1. Lazy Loading (Default)
    print(f'\n#--------------------------- ℹ️ Lazy Loading (Default) ---------------------------------#\n')
    
    # Setting up a Session
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)

    with Session() as session:
        users = session.execute(
            select(User)
        ).scalars().all()

        # Looping through Users
        for user in users:
            print(f'User: {user.name}')
            # Now Accessing user.posts here triggers a separate SELECT for each user
            for post in user.posts:
                print(f'   - Post: {post.title}')

            print(f'\n    - Tags for {user.name}\'s first post: if any')
            if user.posts:
                # Accessing post.tags here triggers another SELECT for each post
                for tag in user.posts[0].tags:
                    print(f'      - Tag: {tag.name}')
            else:
                print(f'ℹ️ No Posts for this user yet')
    
    # 2. Eager Loading with joinedload
    print(f'\n#--------------------------- ℹ️ Eager Loading with joinedload ---------------------------------#\n')
    
    
    with Session() as session:
        # Using one query a JOIN to fetch users and their posts
        print(f'\nℹ️ Eager Loading for User -> Posts\n')
        users_with_posts = session.execute(
            select(User).options(joinedload(User.posts))
        ).unique().scalars().all()

        for user in users_with_posts:
            print(f'User: {user.name}, Posts loaded: {len(user.posts)}')
            # No additional query here for user.posts
            for post in user.posts:
                print(f'   - Post: {post.title}')
            
        print(f'\nℹ️ Eager Loading for User -> Posts -> Tags\n')
        users_with_posts_and_tags = session.execute(
            select(User).options(joinedload(User.posts).joinedload(Post.tags))
        ).unique().scalars().all()

        for user in users_with_posts_and_tags:
            print(f'User: {user.name}, Posts loaded: {len(user.posts)}')
            for post in user.posts:
                print(f'.   - Post: {post.title}, Tags loaded: {len(post.tags)}')
                if post.tags:
                    for tag in post.tags:
                        print(f'      - Tag: {tag.name}')
            
    
    # 3.  Eager Loading with subqueryload for User -> Posts
    print(f'\n#--------------------------- ℹ️ Eager Loading with subqueryload ---------------------------------#\n')
    with Session() as session: 
        # Two queries: one for users, and one for posts using subquery
        users = session.execute(
            select(User).options(subqueryload(User.posts))
        ).scalars().all()

        for user in users:
            print(f'User: {user.name}, Posts loaded: {len(user.posts)}')
            # No additional queries here for user.posts
            for post in user.posts:
                print(f'   - Post: {post.title}')
    
    # 4. Eager Loading with selectinload (Recommended for collection)
    print(f'\n#--------------------------- ℹ️ Eager Loading with selectinload (Recommended) ---------------------------------#\n')
    with Session() as session: 
        # Two queries: one for users, and one for posts using an IN clause (very efficient)
        users = session.execute(
            select(User).options(selectinload(User.posts))
        ).scalars().all()

        for user in users:
            print(f'User: {user.name}, Posts loaded: {len(user.posts)}')
            # No additional queries here for user.posts
            for post in user.posts:
                print(f'   - Post: {post.title}')
            
    # 5. Combined Eager Loading (User -> Posts -> Tags)
    print(f'\n#--------------------------- ℹ️ Eager Loading Combined (User -> Posts -> Tags) --------------------#\n')
    with Session() as session: 
        # Fetch users, their posts, and posts' tags in efficient queries
        users = session.execute(
            select(User).options(
                selectinload(User.posts).selectinload(Post.tags) # Chain selectinload for nested collections
            )
        ).scalars().all()
        for user in users:
            print(f"User: {user.name}")
            for post in user.posts:
                tag_names = [tag.name for tag in post.tags]
                print(f"  - Post: {post.title}, Tags: {', '.join(tag_names) if tag_names else 'None'}")
        

    # 6. Cascade "delete-orphan" demonstration
    print("\n#--------------- ℹ️ Cascade 'delete-orphan' Demo (removing a post from user.posts) --------------------#")
    with Session() as session:
        alice = session.execute(select(User).where(User.name == "Alice")).scalar_one_or_none()
        if alice and alice.posts:
            original_post_count = session.query(Post).count()
            print(f"ℹ️ Initial total posts: {original_post_count}")
            post_to_remove = alice.posts[0] # Get Alice's first post
            print(f"ℹ️ Removing '{post_to_remove.title}' from Alice's posts collection...")
            alice.posts.remove(post_to_remove) # This marks post_to_remove as an orphan
            session.commit() # The orphaned post will be deleted here            
            print(f"✅ Post '{post_to_remove.title}' should now be deleted from DB.")
            new_post_count = session.query(Post).count()
            print(f"ℹ️ New total posts: {new_post_count}")
            # Verify the specific post is gone
            if not session.execute(select(Post).where(Post.id == post_to_remove.id)).scalar_one_or_none():
                print(f"✅ Verification: Post with ID {post_to_remove.id} is indeed gone.")
        else:
            print("ℹ️ Alice or her posts not found for cascade demo.")

    # 7. Cascade "delete" demonstration (User deleted, associated posts deleted)
    print("\n#--- ℹ️ Cascade 'delete' Demo (deleting a user) ---#")
    with Session() as session:
        # We need a fresh user for this to avoid affecting previous tests
        user_temp = User(name="Temporary User", email="temp@example.com")
        session.add(user_temp)
        session.flush() # Flush to get ID, but don't commit yet
        temp_post1 = Post(title="Temp Post 1", content="Content", author=user_temp)
        temp_post2 = Post(title="Temp Post 2", content="Content", author=user_temp)
        session.add_all([temp_post1, temp_post2])
        session.commit()
        print(f"✅ Created Temporary User with ID {user_temp.id} and 2 posts.")

        # Now delete the user
        session.delete(user_temp)
        session.commit() # This will delete user_temp and temp_post1, temp_post2 due to cascade="all, delete-orphan"
        print(f"✅ Deleted Temporary User. Posts for this user should also be gone.")

        # Verify posts are gone
        if not session.execute(select(Post).where(Post.user_id == user_temp.id)).first():
            print("✅ Verification: Temporary User's posts are indeed gone.")
        else:
            print("ℹ️ Verification: Temporary User's posts still exist (cascade issue?).")

# Main Execution Block
if __name__ == "__main__":
    # Create an Engine
    engine = create_engine(DATABASE_URL, echo=True)
    # Setup Data
    setup_orm_data_for_relationships(engine)
    # Perform Operations
    perform_relationship_operations(engine)
```

### Key Components of the Code

#### 1. Database Configuration and Models

The code starts by configuring a connection to a PostgreSQL database using `sqlalchemy.create_engine`. It then defines the ORM models:

- **`User`**: Represents a user. It has a **one-to-many** relationship with `Post` through the `posts: Mapped[List['Post']] = relationship(...)` line. The `cascade='all, delete-orphan'` argument is crucial; it means that if a `Post` is removed from a `User`'s `posts` list, that `Post` will be deleted from the database. It also ensures that when a `User` is deleted, all their associated `Posts` are also deleted.
    
- **`Post`**: Represents a blog post. It has a **many-to-one** relationship with `User` (`author: Mapped[Optional['User']] = relationship(...)`) and a **many-to-many** relationship with `Tag` (`tags: Mapped[List['Tag']] = relationship(...)`). The `user_id` is a `ForeignKey` linking it to the `users` table.
    
- **`Tag`**: Represents a tag for a post. It has a **many-to-many** relationship with `Post`.
    
- **`post_tags_association`**: This `Table` object is a core part of the many-to-many relationship. It's an explicit **association table** that links `posts` and `tags` via foreign keys, without needing a full ORM model for itself.
    

#### 2. Data Setup and Demonstration

The `setup_orm_data_for_relationships` function is a helper that drops existing tables, creates new ones based on the defined models, and populates them with sample data (users, posts, and tags). It establishes the various relationships by assigning posts to users and tags to posts before committing them to the database.

---

### Eager Loading Strategies Explained

A major focus of the code is to show how to handle the performance problem known as the "**N+1 problem**." This occurs in ORMs when you query for a list of parent objects (e.g., `User`s) and then, in a loop, access a related collection (e.g., each user's `posts`). This results in one query to get the parent objects and then N additional queries (one for each parent) to get the related data. Eager loading solves this by fetching all the related data in a more efficient manner, usually with fewer queries.

Here are the different eager loading strategies demonstrated in the code:

#### 1. Lazy Loading (Default)

This is SQLAlchemy's default behavior. When you query for `User` objects, SQLAlchemy only fetches the user data. The related `posts` are not loaded until you explicitly access the `user.posts` attribute. The code demonstrates how this can lead to multiple queries inside a loop, which is inefficient.

#### 2. `joinedload`

`joinedload` performs a **`JOIN`** operation with the related table(s) in a single SQL query. It's very efficient when fetching a limited number of parent objects and their related children.

- `select(User).options(joinedload(User.posts))`: This executes a single `SELECT...JOIN` query to fetch all users and their posts simultaneously.
    
- You can chain `joinedload` to fetch nested relationships, like `joinedload(User.posts).joinedload(Post.tags)`, which joins all three tables (`users`, `posts`, and `post_tags`).
    

#### 3. `subqueryload`

`subqueryload` performs two separate queries: one for the parent objects and a second query using a **`subquery`** to fetch all related objects for the parents. This can be more efficient than `joinedload` for one-to-many relationships, especially when the parent query has a `LIMIT` clause.

#### 4. `selectinload`

This is the recommended strategy for loading collections (one-to-many or many-to-many relationships). It's similar to `subqueryload` in that it uses two queries, but the second query uses an **`IN`** clause to fetch all related objects for all parent objects in a single efficient query. For example, it would fetch all posts where the `user_id` is in the list of IDs from the first query (`SELECT * FROM posts WHERE user_id IN (1, 2, 3...)`).

---

### Cascade Operations

The last part of the code demonstrates **cascade operations** set up on the `User.posts` relationship:

- **`delete-orphan`**: The code shows that when a `Post` object is removed from a `User`'s `posts` list (`alice.posts.remove(post_to_remove)`), the post is automatically deleted from the database upon `session.commit()`.
    
- **`delete`**: The `cascade` setting also includes a `delete` behavior, which is a standard cascade. When a `User`is deleted (`session.delete(user_temp)`), all associated `Post` objects are also automatically deleted.

## Different Eager Loading Strategies

Sure, let's break down the different versions of eager loading in SQLAlchemy, a technique used to solve the "N+1 problem" by fetching related data more efficiently. The main strategies are `joinedload`, `subqueryload`, and `selectinload`.

---

### 1. `joinedload`

`joinedload` fetches all related data in a single SQL query by performing an `OUTER JOIN` on the related tables.

How it works:

The ORM executes one SELECT statement that joins the primary table with the related tables. This is often the simplest and most common approach.

Example:

session.query(User).options(joinedload(User.posts))

This generates a single query: SELECT users.*, posts.* FROM users LEFT OUTER JOIN posts ON users.id = posts.user_id.

**When to use it:**

- When you have a **small number of related objects** per parent object.
    
- When you need to **filter or order on the related table**.
    
- It's particularly good for **one-to-one** and **many-to-one** relationships.
    
- It's useful for simple, shallow relationships.
    

**Drawbacks:**

- Can lead to a **Cartesian product** if a parent object has many related children, resulting in a large number of rows and increased memory usage.
    
- The generated SQL can become complex and slow with multiple joins.
    

---

### 2. `subqueryload`

`subqueryload` executes a separate `SELECT` statement for the related objects, using a subquery to filter by the primary keys of the parent objects.5

**How it works:**

1. The first query fetches the primary objects (e.g., `User`s).
    
2. The second query then uses a `WHERE` clause with a subquery (`WHERE posts.user_id IN (SELECT id FROM users ...)`) to fetch all the related objects (e.g., `Post`s) in a single batch.
    

Example:

session.query(User).options(subqueryload(User.posts))

This results in two queries:

1. `SELECT users.id, users.name FROM users`
    
2. `SELECT posts.id, posts.title, posts.user_id FROM posts WHERE posts.user_id IN (SELECT users.id FROM users)`
    

**When to use it:**

- When you have a **large number of parent objects** but their related collections are relatively small.
    
- When the parent query includes a `LIMIT` or `OFFSET` clause. `joinedload` can produce incorrect results in this scenario because the `LIMIT` is applied after the join.
    
- It's good for **one-to-many** relationships where a `JOIN` would be inefficient.
    

**Drawbacks:**

- The subquery can be a performance bottleneck if the primary key list is very large.
    

---

### 3. `selectinload`

`selectinload` is a more modern and generally **recommended strategy for loading collections** (one-to-many and many-to-many). It's similar to `subqueryload` but uses an `IN` clause instead of a subquery.

**How it works:**

1. The first query fetches the primary objects (e.g., `User`s).
    
2. SQLAlchemy extracts the primary keys from these objects.
    
3. The second query fetches all related objects (e.g., `Post`s) using a simple `WHERE IN` clause on the primary keys.
    

Example:

session.query(User).options(selectinload(User.posts))

This results in two queries:

1. `SELECT users.id, users.name FROM users`
    
2. `SELECT posts.id, posts.title, posts.user_id FROM posts WHERE posts.user_id IN (<list of user IDs from query 1>)`
    

**When to use it:**

- This is the **default recommendation for loading collections** (one-to-many and many-to-many) because it's often the most efficient.
    
- It avoids the complex joins of `joinedload` and the potential subquery overhead of `subqueryload`.
    
- It handles nested eager loading well (`selectinload(User.posts).selectinload(Post.tags)`), chaining the `IN`clause queries.
    

**Drawbacks:**

- Can be less efficient for **many-to-one** relationships, where `joinedload` is often better.
    
- The `IN` clause can become very long, potentially exceeding SQL's maximum query length if there are a massive number of parent objects.
    

### Comparison Table

|Strategy|SQL Query Type|Performance|Best Use Case|
|---|---|---|---|
|**`joinedload`**|**Single `SELECT` with `JOIN`**|Excellent for simple, shallow relationships with a few related items.|**One-to-one** and **many-to-one**relationships. Filtering/ordering on related tables.|
|**`subqueryload`**|**Two `SELECT`statements (one with a subquery)**|Good for one-to-many collections, especially with `LIMIT`or `OFFSET`.|**One-to-many** collections where a join would be inefficient.|
|**`selectinload`**|**Two `SELECT`statements (one with an `IN` clause)**|**Generally the best for loading collections** due to its efficiency and simplicity.|**Collections** (`one-to-many`, `many-to-many`). Avoids performance issues of joins.|


## Code Breakdown - SQLite Implementation

```python
import os
import datetime 
from typing import List, Optional 
from sqlalchemy import create_engine, ForeignKey, String, Integer, Boolean, DateTime, Table, Column 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker 
from sqlalchemy.sql import select 
from sqlalchemy.orm import joinedload, subqueryload, selectinload # Eager loading Strategies

## Configuration for Database Connection 
# SQLite uses a file-based database.
# The 'relationships.db' file will be created in the same directory as the script.
DATABASE_URL = "sqlite:///relationships.db"

# Defining the Declarative Base Class
class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""
    pass

# Association Table for Many to Many 
# This is a core table definition, no an ORM Model
# It explicitly defines the intermediate table for the many-to-many relationship
post_tags_association = Table(
    "post_tags",
    Base.metadata, # Associate with the same metadata as ORM models
    Column("post_id", ForeignKey('posts.id'), primary_key=True),
    Column("tag_id", ForeignKey('tags.id'), primary_key=True),
)

# Defining ORM Models
class User(Base):
    """ORM Model for User Table"""
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # One-to-Many relationship with Post
    posts: Mapped[List['Post']] = relationship(back_populates='author', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'User(id={self.id!r}, name={self.name!r}, email={self.email!r})'
    
class Post(Base):
    """ORM Model for Post Table"""
    __tablename__ = 'posts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))

    # Many-to-One relationship with User
    author: Mapped[Optional['User']] = relationship(back_populates='posts')

    # Many-to-Many relationship with Tag
    tags: Mapped[List['Tag']] = relationship(secondary=post_tags_association, back_populates='posts')

    def __repr__(self) -> str:
        return f'Post(id={self.id!r}, title={self.title!r})'
    
class Tag(Base):
    """ORM Model for Tag Table"""
    __tablename__ = 'tags'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    
    # Many-to-May relationship with Post
    posts: Mapped[List['Post']] = relationship(secondary=post_tags_association, back_populates='tags')

    def __repr__(self) -> str:
        return f'Tag(id={self.id!r}, name={self.name!r})'    
    

# Helper function to setup and populate data
def setup_orm_data_for_relationships(engine):
    """Setting up the Data Tables with Data"""
    print(f'\n#------------------------------- ℹ️ Setting Up Tables with data ---------------------------------#\n')
    # Dropping all tables if exists
    Base.metadata.drop_all(engine)
    # Creating all tables 
    Base.metadata.create_all(engine)    
    print(f'✅ Database Tables Creted Successfully')

    # Setting up a Session
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)

    with Session() as session:
        # Create Users
        user1 = User(name="Alice", email="alice@example.com")
        user2 = User(name="Bob", email="bob@example.com")
        session.add_all([user1, user2])
        session.commit()

        # Create posts and assign to users
        # Note: We can create posts and assign author directly
        post1 = Post(title="Alice's First Post", content="Content for A1", author=user1)
        post2 = Post(title="Bob's Important Post", content="Content for B1", author=user2)
        post3 = Post(title="Alice's Second Post", content="Content for A2", author=user1)
        post4 = Post(title="Standalone Post", content="No author yet") # Will have user_id=None
        session.add_all([post1, post2, post3, post4])
        session.commit()

        # Create tags
        tag_python = Tag(name="Python")
        tag_sqlalchemy = Tag(name="SQLAlchemy")
        tag_webdev = Tag(name="WebDev")
        session.add_all([tag_python, tag_sqlalchemy, tag_webdev])
        session.commit()

        # Associate posts with tags (Many-to-Many)
        # post1 (Alice's First Post) will have Python and SQLAlchemy tags
        post1.tags.append(tag_python)
        post1.tags.append(tag_sqlalchemy)
        # post2 (Bob's Important Post) will have Python and WebDev tags
        post2.tags.append(tag_python)
        post2.tags.append(tag_webdev)
        # post3 (Alice's Second Post) will have SQLAlchemy tag
        post3.tags.append(tag_sqlalchemy)

        session.commit()
        print(f'✅ Initial Data Populated for Relationships Examples.....')

# Perform Relationship and Loading Strategy Examples
def perform_relationship_operations(engine):
    """Performing Relationship and Loading Strategy Examples"""
    print(f'\n#-------------------------- ℹ️ Relationship Operations and Loading Strategies -------------------------#\n')

    # 1. Lazy Loading (Default)
    print(f'\n#--------------------------- ℹ️ Lazy Loading (Default) ---------------------------------#\n')
    
    # Setting up a Session
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)

    with Session() as session:
        users = session.execute(
            select(User)
        ).scalars().all()

        # Looping through Users
        for user in users:
            print(f'User: {user.name}')
            # Now Accessing user.posts here triggers a separate SELECT for each user
            for post in user.posts:
                print(f'   - Post: {post.title}')

            print(f'\n    - Tags for {user.name}\'s first post: if any')
            if user.posts:
                # Accessing post.tags here triggers another SELECT for each post
                for tag in user.posts[0].tags:
                    print(f'      - Tag: {tag.name}')
            else:
                print(f'ℹ️ No Posts for this user yet')
    
    # 2. Eager Loading with joinedload
    print(f'\n#--------------------------- ℹ️ Eager Loading with joinedload ---------------------------------#\n')
    
    
    with Session() as session:
        # Using one query a JOIN to fetch users and their posts
        print(f'\nℹ️ Eager Loading for User -> Posts\n')
        users_with_posts = session.execute(
            select(User).options(joinedload(User.posts))
        ).unique().scalars().all()

        for user in users_with_posts:
            print(f'User: {user.name}, Posts loaded: {len(user.posts)}')
            # No additional query here for user.posts
            for post in user.posts:
                print(f'   - Post: {post.title}')
            
        print(f'\nℹ️ Eager Loading for User -> Posts -> Tags\n')
        users_with_posts_and_tags = session.execute(
            select(User).options(joinedload(User.posts).joinedload(Post.tags))
        ).unique().scalars().all()

        for user in users_with_posts_and_tags:
            print(f'User: {user.name}, Posts loaded: {len(user.posts)}')
            for post in user.posts:
                print(f'.   - Post: {post.title}, Tags loaded: {len(post.tags)}')
                if post.tags:
                    for tag in post.tags:
                        print(f'      - Tag: {tag.name}')
            
    
    # 3.  Eager Loading with subqueryload for User -> Posts
    print(f'\n#--------------------------- ℹ️ Eager Loading with subqueryload ---------------------------------#\n')
    with Session() as session: 
        # Two queries: one for users, and one for posts using subquery
        users = session.execute(
            select(User).options(subqueryload(User.posts))
        ).scalars().all()

        for user in users:
            print(f'User: {user.name}, Posts loaded: {len(user.posts)}')
            # No additional queries here for user.posts
            for post in user.posts:
                print(f'   - Post: {post.title}')
    
    # 4. Eager Loading with selectinload (Recommended for collection)
    print(f'\n#--------------------------- ℹ️ Eager Loading with selectinload (Recommended) ---------------------------------#\n')
    with Session() as session: 
        # Two queries: one for users, and one for posts using an IN clause (very efficient)
        users = session.execute(
            select(User).options(selectinload(User.posts))
        ).scalars().all()

        for user in users:
            print(f'User: {user.name}, Posts loaded: {len(user.posts)}')
            # No additional queries here for user.posts
            for post in user.posts:
                print(f'   - Post: {post.title}')
            
    # 5. Combined Eager Loading (User -> Posts -> Tags)
    print(f'\n#--------------------------- ℹ️ Eager Loading Combined (User -> Posts -> Tags) --------------------#\n')
    with Session() as session: 
        # Fetch users, their posts, and posts' tags in efficient queries
        users = session.execute(
            select(User).options(
                selectinload(User.posts).selectinload(Post.tags) # Chain selectinload for nested collections
            )
        ).scalars().all()
        for user in users:
            print(f"User: {user.name}")
            for post in user.posts:
                tag_names = [tag.name for tag in post.tags]
                print(f"  - Post: {post.title}, Tags: {', '.join(tag_names) if tag_names else 'None'}")
        

    # 6. Cascade "delete-orphan" demonstration
    print("\n#--------------- ℹ️ Cascade 'delete-orphan' Demo (removing a post from user.posts) --------------------#")
    with Session() as session:
        alice = session.execute(select(User).where(User.name == "Alice")).scalar_one_or_none()
        if alice and alice.posts:
            original_post_count = session.query(Post).count()
            print(f"ℹ️ Initial total posts: {original_post_count}")
            post_to_remove = alice.posts[0] # Get Alice's first post
            print(f"ℹ️ Removing '{post_to_remove.title}' from Alice's posts collection...")
            alice.posts.remove(post_to_remove) # This marks post_to_remove as an orphan
            session.commit() # The orphaned post will be deleted here            
            print(f"✅ Post '{post_to_remove.title}' should now be deleted from DB.")
            new_post_count = session.query(Post).count()
            print(f"ℹ️ New total posts: {new_post_count}")
            # Verify the specific post is gone
            if not session.execute(select(Post).where(Post.id == post_to_remove.id)).scalar_one_or_none():
                print(f"✅ Verification: Post with ID {post_to_remove.id} is indeed gone.")
        else:
            print("ℹ️ Alice or her posts not found for cascade demo.")

# Main Execution Block
if __name__ == "__main__":
    # Create an Engine
    engine = create_engine(DATABASE_URL, echo=True)
    # Setup Data
    setup_orm_data_for_relationships(engine)
    # Perform Operations
    perform_relationship_operations(engine)
```

### Key Difference

+ **Datase Connection String**: This is the main difference between the two scripts (Postgres version and SQLite version)



