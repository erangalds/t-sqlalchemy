# CRUD Operations (Create, Read, Update, Delete)

Right, so now I have showed you how to define the schemas and tables and get them created with SQLAlchemy, now I would like to show you how to perform CRUD operations with SQLAlchemy Core's expression language.

**Key SQLAlchemy Core Constructs for CRUD:**

- **`insert()`**: Constructs an `INSERT` statement.
- **`select()`**: Constructs a `SELECT` statement.
- **`update()`**: Constructs an `UPDATE` statement.
- **`delete()`**: Constructs a `DELETE` statement.
- **`where()`**: Adds a `WHERE` clause to a `SELECT`, `UPDATE`, or `DELETE` statement.
- **`order_by()`**: Adds an `ORDER BY` clause to a `SELECT` statement.
- **`limit()`, `offset()`**: Adds `LIMIT` and `OFFSET` clauses.
- **`Connection`**: The object used to execute statements. Obtained from `engine.connect()`.
- **`Result`**: The object returned by `connection.execute()`, allowing you to fetch rows.
    - `all()`: Fetches all rows as a list of `Row` objects.
    - `first()`: Fetches the first row.
    - `scalar()`: Fetches the scalar value of the first column of the first row.
    - `scalars()`: Fetches the scalar values of the first column of all rows.


Let us dive straight into the python implementation. 

## Code Breakdown

### Postgres Implementation

```python
import os 
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import select, insert, update, delete
import datetime

## Configuration for Database Connection 
# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "my_sqlalchemy_db"
DB_USER = "sqlalchemy"
DB_PASSWORD = "sqlalchemy_password"

# Create connection string (using psycopg3)
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

## Database Schema Definition
metadata = MetaData()

users_table = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(50), nullable=False),
    Column("email", String(100), nullable=False, unique=True),
    Column("is_active", Boolean, default=True),
    Column("created_at", DateTime, default=datetime.datetime.now),
)

posts_table = Table(
    "posts", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", String(200), nullable=False),
    Column("content", String, nullable=False),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("published_at", DateTime, default=datetime.datetime.now),
)

# -- Helper function to setup and get engine --
def get_engine(db_url: str, echo: bool = True):
    """Create and return a SQLAlchemy engine."""
    engine = create_engine(db_url, echo=echo)
    print(f"✅ Engine created for database: {db_url}")
    # Create Tables if they do not exist
    metadata.create_all(engine)
    print(f"✅ database ready for CRUD operation: {db_url}")    
    return engine

# -- Function to perform CRUD ---- 
def perform_crud_operations(engine):
    """Perform basic CRUD operations."""
    with engine.connect() as connection:
        # ------------------------------- CREATE: Insert New Users -------------------------------
        print("🔄 Inserting new users..")
        # Insert a Single User
        insert_user1 = users_table.insert().values(
            name="Alice", 
            email="alice@example.com", 
            is_active=True, 
            created_at=datetime.datetime.now()
        )
        result_user1 = connection.execute(insert_user1)
        print(f"✅ User Alice inserted with ID: {result_user1.inserted_primary_key[0]}")
        alice_id = result_user1.inserted_primary_key[0]
        connection.commit()  # Ensure changes are saved
        # Insert Multiple Users
        insert_users = users_table.insert().values([
            {"name": "Bob", "email": "bob@example.com", "is_active": True, "created_at": datetime.datetime.now()},
            {"name": "Charlie", "email": "charlie@example.com", "is_active": False, "created_at": datetime.datetime.now()},
            {"name": "David", "email": "david@example.com", "is_active": False, "created_at": datetime.datetime.now()},
        ])
        result_users = connection.execute(insert_users)
        print(f"✅ Multiple users inserted, Results: {result_users.inserted_primary_key_rows}")
        # Get IDs of inserted users
        select_users = select(users_table.c.id).where(users_table.c.email.in_(
            ["bob@example.com", "charlie@example.com", "david@example.com"]
        ))
        result_select_users = connection.execute(select_users)
        user_ids = result_select_users.fetchall()
        user_ids = [user_id[0] for user_id in user_ids]  # Extract IDs from tuples
        print(f"✅ User IDs of inserted users: {user_ids}")
        bob_id = user_ids[0]
        print(f"✅ Bob's ID: {bob_id}")
        charlie_id = user_ids[1]
        print(f"✅ Charlie's ID: {charlie_id}")
        david_id = user_ids[2]
        print(f"✅ David's ID: {david_id}")
                
        # ------------------------------- CREATE: Insert New Posts -------------------------------
        print("🔄 Inserting new posts..")
        # Insert Multiple Posts
        inserting_posts = posts_table.insert().values([
            {"title": "Alices First Post", "content": "This is Alice's first post.", "user_id": alice_id, "published_at": datetime.datetime.now()},
            {"title": "Bobs First Post", "content": "This is Bob's first post.", "user_id": bob_id, "published_at": datetime.datetime.now()},
            {"title": "Charlies First Post", "content": "This is Charlie's first post.", "user_id": charlie_id, "published_at": datetime.datetime.now()},
            {"title": "Davids First Post", "content": "This is David's first post.", "user_id": david_id, "published_at": datetime.datetime.now()},
        ])
        result_posts = connection.execute(inserting_posts)
        print(f"✅ Multiple posts inserted, total rows affected: {result_posts.rowcount}")

        # Commit the transaction
        connection.commit() # Ensure changes are saved

        # ----------------------------- READ: Query Users -----------------------------
        print("🔄 Querying users..")
        select_all_users = select(users_table)
        result_users = connection.execute(select_all_users)
        users = result_users.fetchall()
        
        print(f"✅ Total users found: {len(users)}")
        # Iterating through the results
        for user in users:
            print(f"User ID: {user.id}, Name: {user.name}, Email: {user.email}, Active: {user.is_active}, Created At: {user.created_at}")
        
        # ----------------------------- SELECT with Where -----------------------------
        print("🔄 Querying active users..")
        select_active_users = select(users_table).where(users_table.c.is_active == True).order_by(users_table.c.name)
        result_active_users = connection.execute(select_active_users)
        active_users = result_active_users.fetchall()

        print(f"✅ Total active users found: {len(active_users)}")
        for user in active_users:
            print(f"Active User ID: {user.id}, Name: {user.name}, Email: {user.email}, Created At: {user.created_at}")
        
        print("🔄 Querying users with specific User ID..")
        # Querying a specific user by ID
        select_user_by_id = select(users_table.c.name).where(users_table.c.id == alice_id)
        result_user_by_id = connection.execute(select_user_by_id)
        user_name = result_user_by_id.scalar()
        print(f"✅ User with ID {alice_id} found: {user_name}")

        print("Quering 1st two Posts..")
        select_first_two_posts = select(posts_table).limit(2)
        result_first_two_posts = connection.execute(select_first_two_posts)
        first_two_posts = result_first_two_posts.fetchall()

        for post in first_two_posts:
            print(f"Post ID: {post.id}, Title: {post.title}, Content: {post.content}, User ID: {post.user_id}, Published At: {post.published_at}") 

        print("🔄 Querying posts by User ID..")
        select_posts_by_user_id = select(posts_table.c.title, users_table.c.name).join(users_table, posts_table.c.user_id == users_table.c.id).where(users_table.c.id == alice_id).order_by(posts_table.c.published_at.desc())
        # Execute the query to get posts by user ID
        result_posts_by_user_id = connection.execute(select_posts_by_user_id)
        posts_by_user_id = result_posts_by_user_id.fetchall()

        for post in posts_by_user_id:
            print(f"Post Title: {post.title}, User Name: {post.name}")

        # ----------------------------- UPDATE: Update User Information -----------------------------
        print("🔄 Updating user information..")
        update_user = users_table.update().where(users_table.c.email == "bob@example.com").values(name="Robert")
        result_update_user = connection.execute(update_user)
        # Commit the transaction
        connection.commit()
        print(f"✅ User Bob updated, rows affected: {result_update_user.rowcount}")
        # Verify the update
        select_updated_user = select(users_table).where(users_table.c.email == "bob@example.com")
        result_updated_user = connection.execute(select_updated_user)
        updated_user = result_updated_user.fetchone()
        print(f"Updated User: ID: {updated_user.id}, Name: {updated_user.name}, Email: {updated_user.email}")

        print("🔄 Updating Multiple Users..")
        update_multiple_users = users_table.update().where(users_table.c.is_active == False).values(is_active=True)
        result_update_multiple_users = connection.execute(update_multiple_users)
        # Commit the transaction
        connection.commit()
        print(f"✅ Multiple users updated, rows affected: {result_update_multiple_users.rowcount}")
        # Verify the update
        select_updated_users = select(users_table).where(users_table.c.is_active == True)
        result_updated_users = connection.execute(select_updated_users)
        updated_users = result_updated_users.fetchall()
        print(f"✅ Total active users after update: {len(updated_users)}")
        
        # ----------------------------- DELETE: Delete Users and Posts -----------------------------
        print("🔄 Deleting users and posts..")
        # Deleting a specific post
        delete_post = posts_table.delete().where(posts_table.c.title == "Bob's First Post")
        result_delete_post = connection.execute(delete_post)
        # Commit the transaction
        connection.commit()
        print(f"✅ Post 'Bob's First Post' deleted, rows affected: {result_delete_post.rowcount}")

        # Deleting Posts for a specific user
        # SQLAlchemy Core does not support cascading deletes directly, we need to set DELETE CASCADE in the ForeignKey constraint
        # Let's check this
        delete_posts_by_user = posts_table.delete().where(posts_table.c.user_id == charlie_id)
        result_delete_posts_by_user = connection.execute(delete_posts_by_user)
        # Commit the transaction
        connection.commit()
        print(f"✅ Posts by user 'Charlie' deleted, rows affected: {result_delete_posts_by_user.rowcount}")
        # Verify the deletion
        select_deleted_posts = select(posts_table).where(posts_table.c.user_id == charlie_id)
        result_deleted_posts = connection.execute(select_deleted_posts)
        deleted_posts = result_deleted_posts.fetchall()
        if not deleted_posts:
            print("✅ All posts by user 'Charlie' successfully deleted.")

        delete_user = delete(users_table).where(users_table.c.name == "Charlie")
        result_delete_user = connection.execute(delete_user)
        # Commit the transaction
        connection.commit()
        print(f"✅ User 'Charlie' deleted, rows affected: {result_delete_user.rowcount}")
        # Verify the deletion
        select_deleted_user = select(users_table).where(users_table.c.name == "Charlie")
        result_deleted_user = connection.execute(select_deleted_user)
        deleted_user = result_deleted_user.fetchone()
        if deleted_user is None:
            print("✅ User 'Charlie' successfully deleted.")
        else:
            print(f"❌ User 'Charlie' still exists: {deleted_user.name}")
        # Verify with total users
        select_all_users_after_delete = select(users_table.c.name)
        result_all_users_after_delete = connection.execute(select_all_users_after_delete)
        all_users_after_delete = result_all_users_after_delete.fetchall()
        print(f"✅ Total users after deletion: {len(all_users_after_delete)}")
        # Verify with total posts
        select_all_posts = select(posts_table.c.title)
        result_all_posts = connection.execute(select_all_posts)
        all_posts = result_all_posts.fetchall()
        print(f"✅ Total posts after deletion: {len(all_posts)}")       


if __name__ == "__main__":
    engine = get_engine(DATABASE_URL)
    perform_crud_operations(engine)

```

---

#### 1. Database Configuration and Connection

The script begins by setting up the connection parameters for a PostgreSQL database.

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: These variables hold the details needed to connect to the database.
    
- `DATABASE_URL`: This string is constructed using the connection parameters. It specifies the database driver to use (`postgresql+psycopg`), the user, password, host, port, and database name.
    
- `get_engine()`: This function takes the `DATABASE_URL` and creates an **engine**, which is the central object that manages the database connection. The `echo=True` parameter tells SQLAlchemy to print the SQL statements it executes to the console, which is very useful for debugging. The function also calls `metadata.create_all(engine)` to create the `users` and `posts` tables in the database if they don't already exist.
    

---

#### 2. Database Schema Definition

The code defines the structure of two tables: `users` and `posts`.

- `metadata = MetaData()`: This object acts as a container for all the table definitions.
    
- `users_table` and `posts_table`: These are `Table` objects that define the database schema.
    
    - `Column`: This class defines a column with its name, data type (e.g., `Integer`, `String`, `Boolean`), and various constraints.
        
    - `primary_key=True`: This specifies the primary key for the table.
        
    - `autoincrement=True`: This automatically increments the ID for each new entry.
        
    - `unique=True`: This enforces that no two users can have the same email address.
        
    - `ForeignKey("users.id")`: This is a crucial line that establishes a **relationship** between the `posts`table and the `users` table. The `user_id` column in the `posts` table references the `id` column in the `users` table, ensuring that every post must belong to a valid user.
        

---

#### 3. CRUD Operations

The `perform_crud_operations()` function demonstrates how to interact with the database using the defined schema. It works within a context manager (`with engine.connect() as connection:`) which automatically handles opening and closing the database connection.

##### **Create (Insert)** ➕

- **Inserting a single row:** `users_table.insert().values(...)` creates an `INSERT` statement, and `connection.execute(...)` sends it to the database. The `inserted_primary_key` property of the result object returns the ID of the newly created user.
    
- **Inserting multiple rows:** You can insert multiple rows in a single operation by passing a list of dictionaries to `values()`.
    
- **`connection.commit()`**: This is called after the insert operations to save the changes to the database permanently.
    

##### **Read (Select)** 📖

- **Selecting all data:** `select(users_table)` generates a basic `SELECT * FROM users` query. The `connection.execute(...)` returns a result object, and `fetchall()` retrieves all the rows as a list of `Row`objects.
    
- **Filtering results:** The `where()` clause is used to filter rows based on a condition, like `users_table.c.is_active == True`. `c` is a shortcut for the table's `columns` collection.
    
- **Joining tables:** `select(...).join(...)` is used to combine data from two tables, `posts` and `users`, based on their `ForeignKey` relationship. This allows the query to retrieve the post title and the user's name in a single result.
    
- **Retrieving specific data:** `fetchone()` retrieves the first row, and `scalar()` retrieves the value of the first column of the first row, which is useful when you expect a single value.
    

##### **Update** ✍️

- `users_table.update().where(...).values(...)`: This constructs an `UPDATE` statement. The `where()` clause specifies which rows to update (e.g., the user with the email `bob@example.com`), and `values()` specifies the new data (e.g., changing the name to "Robert").
    

##### **Delete** 🗑️

- `posts_table.delete().where(...)`: This creates a `DELETE` statement. The `where()` clause is used to specify which rows to remove. The code demonstrates deleting a single post and then all posts for a specific user.
    
- `connection.commit()` is used after all update and delete statements to persist the changes.
    
### SQLite Implementation

```python
Here is the same script, but converted to use SQLite. The core SQLAlchemy syntax for defining the schema and performing CRUD operations remains largely the same, as that is designed to be database-agnostic. The primary changes are in the database connection string.

```python
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import select, insert, update, delete
import datetime

## Configuration for Database Connection 
# SQLite uses a file-based database. The path can be relative or absolute.
# We'll use a file named 'my_sqlite_db.db' in the current directory.
DB_FILE = "my_sqlite_db.db"

# Create connection string for SQLite
DATABASE_URL = f"sqlite:///{DB_FILE}"

## Database Schema Definition
metadata = MetaData()

users_table = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(50), nullable=False),
    Column("email", String(100), nullable=False, unique=True),
    Column("is_active", Boolean, default=True),
    Column("created_at", DateTime, default=datetime.datetime.now),
)

posts_table = Table(
    "posts", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", String(200), nullable=False),
    Column("content", String, nullable=False),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("published_at", DateTime, default=datetime.datetime.now),
)

# -- Helper function to setup and get engine --
def get_engine(db_url: str, echo: bool = True):
    """Create and return a SQLAlchemy engine."""
    # SQLite does not require a driver like psycopg, it is built-in with SQLAlchemy.
    engine = create_engine(db_url, echo=echo)
    print(f"✅ Engine created for database: {db_url}")
    # Create Tables if they do not exist
    metadata.create_all(engine)
    print(f"✅ database ready for CRUD operation: {db_url}")    
    return engine

# -- Function to perform CRUD ---- 
def perform_crud_operations(engine):
    """Perform basic CRUD operations."""
    with engine.connect() as connection:
        # ------------------------------- CREATE: Insert New Users -------------------------------
        print("🔄 Inserting new users..")
        # Insert a Single User
        insert_user1 = users_table.insert().values(
            name="Alice", 
            email="alice@example.com", 
            is_active=True, 
            created_at=datetime.datetime.now()
        )
        result_user1 = connection.execute(insert_user1)
        # For SQLite, inserted_primary_key is available
        print(f"✅ User Alice inserted with ID: {result_user1.inserted_primary_key[0]}")
        alice_id = result_user1.inserted_primary_key[0]
        connection.commit()  # Ensure changes are saved
        # Insert Multiple Users
        insert_users = users_table.insert().values([
            {"name": "Bob", "email": "bob@example.com", "is_active": True, "created_at": datetime.datetime.now()},
            {"name": "Charlie", "email": "charlie@example.com", "is_active": False, "created_at": datetime.datetime.now()},
            {"name": "David", "email": "david@example.com", "is_active": False, "created_at": datetime.datetime.now()},
        ])
        result_users = connection.execute(insert_users)
        # SQLite returns None for inserted_primary_key on multi-row inserts, so we check rowcount.
        print(f"✅ Multiple users inserted, total rows affected: {result_users.rowcount}")
        # Get IDs of inserted users - this is a robust, database-agnostic way to get the IDs
        select_users = select(users_table.c.id).where(users_table.c.email.in_(
            ["bob@example.com", "charlie@example.com", "david@example.com"]
        ))
        result_select_users = connection.execute(select_users)
        user_ids = result_select_users.fetchall()
        user_ids = [user_id[0] for user_id in user_ids]  # Extract IDs from tuples
        print(f"✅ User IDs of inserted users: {user_ids}")
        bob_id = user_ids[0]
        print(f"✅ Bob's ID: {bob_id}")
        charlie_id = user_ids[1]
        print(f"✅ Charlie's ID: {charlie_id}")
        david_id = user_ids[2]
        print(f"✅ David's ID: {david_id}")
                
        # ------------------------------- CREATE: Insert New Posts -------------------------------
        print("🔄 Inserting new posts..")
        # Insert Multiple Posts
        inserting_posts = posts_table.insert().values([
            {"title": "Alices First Post", "content": "This is Alice's first post.", "user_id": alice_id, "published_at": datetime.datetime.now()},
            {"title": "Bobs First Post", "content": "This is Bob's first post.", "user_id": bob_id, "published_at": datetime.datetime.now()},
            {"title": "Charlies First Post", "content": "This is Charlie's first post.", "user_id": charlie_id, "published_at": datetime.datetime.now()},
            {"title": "Davids First Post", "content": "This is David's first post.", "user_id": david_id, "published_at": datetime.datetime.now()},
        ])
        result_posts = connection.execute(inserting_posts)
        print(f"✅ Multiple posts inserted, total rows affected: {result_posts.rowcount}")

        # Commit the transaction
        connection.commit() # Ensure changes are saved

        # ----------------------------- READ: Query Users -----------------------------
        print("🔄 Querying users..")
        select_all_users = select(users_table)
        result_users = connection.execute(select_all_users)
        users = result_users.fetchall()
        
        print(f"✅ Total users found: {len(users)}")
        # Iterating through the results
        for user in users:
            print(f"User ID: {user.id}, Name: {user.name}, Email: {user.email}, Active: {user.is_active}, Created At: {user.created_at}")
        
        # ----------------------------- SELECT with Where -----------------------------
        print("🔄 Querying active users..")
        select_active_users = select(users_table).where(users_table.c.is_active == True).order_by(users_table.c.name)
        result_active_users = connection.execute(select_active_users)
        active_users = result_active_users.fetchall()

        print(f"✅ Total active users found: {len(active_users)}")
        for user in active_users:
            print(f"Active User ID: {user.id}, Name: {user.name}, Email: {user.email}, Created At: {user.created_at}")
        
        print("🔄 Querying users with specific User ID..")
        # Querying a specific user by ID
        select_user_by_id = select(users_table.c.name).where(users_table.c.id == alice_id)
        result_user_by_id = connection.execute(select_user_by_id)
        user_name = result_user_by_id.scalar()
        print(f"✅ User with ID {alice_id} found: {user_name}")

        print("Quering 1st two Posts..")
        select_first_two_posts = select(posts_table).limit(2)
        result_first_two_posts = connection.execute(select_first_two_posts)
        first_two_posts = result_first_two_posts.fetchall()

        for post in first_two_posts:
            print(f"Post ID: {post.id}, Title: {post.title}, Content: {post.content}, User ID: {post.user_id}, Published At: {post.published_at}") 

        print("🔄 Querying posts by User ID..")
        select_posts_by_user_id = select(posts_table.c.title, users_table.c.name).join(users_table, posts_table.c.user_id == users_table.c.id).where(users_table.c.id == alice_id).order_by(posts_table.c.published_at.desc())
        # Execute the query to get posts by user ID
        result_posts_by_user_id = connection.execute(select_posts_by_user_id)
        posts_by_user_id = result_posts_by_user_id.fetchall()

        for post in posts_by_user_id:
            print(f"Post Title: {post.title}, User Name: {post.name}")

        # ----------------------------- UPDATE: Update User Information -----------------------------
        print("🔄 Updating user information..")
        update_user = users_table.update().where(users_table.c.email == "bob@example.com").values(name="Robert")
        result_update_user = connection.execute(update_user)
        # Commit the transaction
        connection.commit()
        print(f"✅ User Bob updated, rows affected: {result_update_user.rowcount}")
        # Verify the update
        select_updated_user = select(users_table).where(users_table.c.email == "bob@example.com")
        result_updated_user = connection.execute(select_updated_user)
        updated_user = result_updated_user.fetchone()
        print(f"Updated User: ID: {updated_user.id}, Name: {updated_user.name}, Email: {updated_user.email}")

        print("🔄 Updating Multiple Users..")
        update_multiple_users = users_table.update().where(users_table.c.is_active == False).values(is_active=True)
        result_update_multiple_users = connection.execute(update_multiple_users)
        # Commit the transaction
        connection.commit()
        print(f"✅ Multiple users updated, rows affected: {result_update_multiple_users.rowcount}")
        # Verify the update
        select_updated_users = select(users_table).where(users_table.c.is_active == True)
        result_updated_users = connection.execute(select_updated_users)
        updated_users = result_updated_users.fetchall()
        print(f"✅ Total active users after update: {len(updated_users)}")
        
        # ----------------------------- DELETE: Delete Users and Posts -----------------------------
        print("🔄 Deleting users and posts..")
        # Deleting a specific post
        delete_post = posts_table.delete().where(posts_table.c.title == "Bob's First Post")
        result_delete_post = connection.execute(delete_post)
        # Commit the transaction
        connection.commit()
        print(f"✅ Post 'Bob's First Post' deleted, rows affected: {result_delete_post.rowcount}")

        # Deleting Posts for a specific user
        delete_posts_by_user = posts_table.delete().where(posts_table.c.user_id == charlie_id)
        result_delete_posts_by_user = connection.execute(delete_posts_by_user)
        # Commit the transaction
        connection.commit()
        print(f"✅ Posts by user 'Charlie' deleted, rows affected: {result_delete_posts_by_user.rowcount}")
        # Verify the deletion
        select_deleted_posts = select(posts_table).where(posts_table.c.user_id == charlie_id)
        result_deleted_posts = connection.execute(select_deleted_posts)
        deleted_posts = result_deleted_posts.fetchall()
        if not deleted_posts:
            print("✅ All posts by user 'Charlie' successfully deleted.")
            
        delete_user = delete(users_table).where(users_table.c.name == "Charlie")
        result_delete_user = connection.execute(delete_user)
        # Commit the transaction
        connection.commit()
        print(f"✅ User 'Charlie' deleted, rows affected: {result_delete_user.rowcount}")
        # Verify the deletion
        select_deleted_user = select(users_table).where(users_table.c.name == "Charlie")
        result_deleted_user = connection.execute(select_deleted_user)
        deleted_user = result_deleted_user.fetchone()
        if deleted_user is None:
            print("✅ User 'Charlie' successfully deleted.")
        else:
            print(f"❌ User 'Charlie' still exists: {deleted_user.name}")
        # Verify with total users
        select_all_users_after_delete = select(users_table.c.name)
        result_all_users_after_delete = connection.execute(select_all_users_after_delete)
        all_users_after_delete = result_all_users_after_delete.fetchall()
        print(f"✅ Total users after deletion: {len(all_users_after_delete)}")
        # Verify with total posts
        select_all_posts = select(posts_table.c.title)
        result_all_posts = connection.execute(select_all_posts)
        all_posts = result_all_posts.fetchall()
        print(f"✅ Total posts after deletion: {len(all_posts)}")       

if __name__ == "__main__":
    engine = get_engine(DATABASE_URL)
    perform_crud_operations(engine)
```

#### Difference betwen SQLite and Postgres Implementations 

### Database Connection and Driver

- **SQLite Script:** The script uses a simple connection string: `sqlite:///my_sqlite_db.db`. This tells SQLAlchemy to connect to a local file named `my_sqlite_db.db`. SQLite is a **serverless** database, meaning there's no separate server process running. The database is a single file on your disk, and the necessary driver is built into Python.
    
- **PostgreSQL Script:** The script uses a more complex connection string: `postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}`. This format specifies a username, password, host, and port because PostgreSQL is a **client-server** database. It requires a separate server process to be running and a dedicated driver like **psycopg** to communicate with it.





