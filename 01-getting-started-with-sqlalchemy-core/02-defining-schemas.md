# Defining Schemas

SQLAlchemy Core provides objects to represent our databasae schema:

+ **`MetaData` object: A container that holds all the schema constructs (tables, sequences, etc.) of a database. It's associated with an `Engine` to perform DDL (Data Definition Language) operations like `CREATE TABLE`. 

+ **`Table` Definition**: Represents a database table. We have to define its name, and then its columns. 

+ **Column**: Represents a column in a database table. We specify its data type (`Integer`, `String`, `DateTime`, `Boolean`, etc), whether its a primary key, nullable etc. 

+ **`PrimaryKeyConstraint`**: Defines which column(s) constitute the primary key of a table. Often, you'll just pass `primary_key=True` to the colume definition.

+ **`ForeignKey`**: Defines a foreign key relationship to a column in another table.

## Creating Tables: `.create_all()`

The `MetaData.create_all(engine)` method iterates through all Table objects associated with the `MetaData` instance and issues `CREATE TABLE` statements to the database via the provided `Engine`.

## Postgres Implementation 
### Code Breakdown


```python
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy import text 
from sqlalchemy.sql import expression 
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

# Define 'users' tabale 
users_table = Table(
    'users', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(100), nullable=False),
    Column('email', String(100), unique=True, nullable=False),
    Column('is_active', Boolean, default=True),
    Column('created_at', DateTime, default=datetime.datetime.now)
)

# Define 'posts' table
posts_table = Table(
    'posts', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('title', String(200), nullable=False),
    Column('content', String, nullable=False),
    Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
    Column('published_at', DateTime, default=datetime.datetime.now)
)

# Defining functions to setup and teardown the database
def setup_database(db_url: str, db_name: str):
    """Setting up Datbase"""
    engine = create_engine(db_url, echo=True) # Create engine with echo=True for debugging

    try: 
        # Dropping existing tables if they exist
        with engine.connect() as connection:
            # Check if tables exists before dropping
            if engine.dialect.has_table(connection, 'posts'):
                posts_table.drop(engine)
                print(f"✅ Table 'posts' dropped successfully.")
            if engine.dialect.has_table(connection, 'users'):
                users_table.drop(engine)
                print(f"✅ Table 'users' dropped successfully.")
            
            # Create tables
            metadata.create_all(engine)
            print(f"✅ Tables 'users' and 'posts' created successfully in database '{db_name}'.")
    except Exception as e:
        print(f"An error occurred while setting up the database: {e}")
    finally:
        if engine:
            engine.dispose()

def teardown_database(db_url: str, db_name: str):
    """Teardown Database"""
    engine = create_engine(db_url, echo=True)  # Create engine with echo=True for debugging

    try:
        with engine.connect() as connection:
            # Drop tables if they exist
            if engine.dialect.has_table(connection, 'posts'):
                posts_table.drop(engine)
                print(f"✅ Table 'posts' dropped successfully.")
            if engine.dialect.has_table(connection, 'users'):
                users_table.drop(engine)
                print(f"✅ Table 'users' dropped successfully.")
    except Exception as e:
        print(f"An error occurred while tearing down the database: {e}")
    finally:
        if engine:
            engine.dispose()

if __name__ == "__main__":
    setup_database(DATABASE_URL, DB_NAME)
    #teardown_database(DATABASE_URL, DB_NAME)  # Uncomment to teardown after testing
```

#### **Database Configuration**

This section sets up the connection details for a **PostgreSQL database**. It defines constants for the **database host**, **port**, **name**, **user**, and **password**. These constants are then used to create a formatted **connection string**, which is essential for SQLAlchemy to connect to the database. The `DATABASE_URL` uses the `postgresql+psycopg` dialect, specifying that it will use the `psycopg` driver to connect to a PostgreSQL database.

#### **Schema Definition**

Here, the script defines the structure of the database tables using SQLAlchemy's **`Table` and `Column` objects**. A **`MetaData` object** is used to store information about the database schema.

- **`users_table`**: This table has an `id` column as the **primary key** that auto-increments, a non-null `name` column, a unique and non-null `email` column, an `is_active` boolean column with a default value of `True`, and a `created_at` datetime column that defaults to the current timestamp.
    
- **`posts_table`**: This table also has an auto-incrementing **primary key `id`**. It contains a `title`, `content`, and a `published_at` datetime column. The most crucial part is the `user_id` column, which is defined as a **foreign key** referencing the `id` column of the `users` table. This establishes a **one-to-many relationship** where one user can have multiple posts.
    

#### **Database Setup Functions**

The script includes two main functions to manage the database state.

- **`setup_database(db_url: str, db_name: str)`**: This function connects to the database using the provided URL. It creates an **`engine`**—a central component in SQLAlchemy that provides connectivity to the database. The `echo=True` argument makes SQLAlchemy **print all SQL commands** it executes, which is useful for debugging. Inside a **`try...except...finally` block**, it safely drops the `posts` and `users` tables if they already exist to ensure a clean slate, then creates them using `metadata.create_all(engine)`. The `finally` block ensures the **engine connection is properly disposed** to free up resources.
    
- **`teardown_database(db_url: str, db_name: str)`**: Similar to the setup function, this function connects to the database and **drops the `posts` and `users` tables** if they exist. It's designed to clean up the database after testing or use.

---

### Core Components Used

- **SQLAlchemy Engine**: The **`create_engine` function** is the starting point for any SQLAlchemy application. It creates a connection pool and a dialect for communicating with a specific database.
    
- **`MetaData`**: Think of `MetaData` as a container for all the tables and related objects in a database. When you call **`metadata.create_all(engine)`**, SQLAlchemy generates the necessary **`CREATE TABLE` SQL statements** for all tables registered with that `MetaData` object and executes them.
    
- **`Table` and `Column`**: These classes are the core of the SQLAlchemy Expression Language. The `Table` object represents a database table, and **`Column` objects** define the individual columns, including their data types, constraints (like `primary_key`, `nullable`, and `unique`), and default values.
    
- **Foreign Key**: The **`ForeignKey('users.id')`** constraint in the `posts_table` is a critical part of relational database design. It enforces **referential integrity**, ensuring that a post can only exist if its `user_id` corresponds to a valid `id` in the `users` table. This prevents orphaned data and maintains data consistency.

## SQLite Implementation 

### Code Breakdown

```python
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, ForeignKey
import datetime

# --- Configuration for Database Connection (Simplified for SQLite) ---
# SQLite is a file-based database, so we just need a file path.
# This will create a file named 'my_sqlite_db.db' in the current directory.
DATABASE_URL = "sqlite:///my_sqlite_db.db"
DB_FILE_NAME = "my_sqlite_db.db"

# --- Database Schema Definition (Remains the same due to SQLAlchemy's abstraction) ---
metadata = MetaData()

# Define 'users' table
users_table = Table(
    'users', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(100), nullable=False),
    Column('email', String(100), unique=True, nullable=False),
    Column('is_active', Boolean, default=True),
    Column('created_at', DateTime, default=datetime.datetime.now)
)

# Define 'posts' table
posts_table = Table(
    'posts', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('title', String(200), nullable=False),
    Column('content', String, nullable=False),
    Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
    Column('published_at', DateTime, default=datetime.datetime.now)
)

# --- Functions to setup and teardown the database ---
def setup_database(db_url: str, db_file: str):
    """Setting up Database for SQLite.
    This function will create the database file and the tables.
    """
    # Create the engine with the SQLite connection string
    engine = create_engine(db_url, echo=True)

    # Checking if the tables already exist
    try: 
        with engine.connect() as connection:
            # Check if tables exist before dropping
            if engine.dialect.has_table(connection, 'posts'):
                posts_table.drop(engine)
                print(f"✅ Table 'posts' dropped successfully.")
            if engine.dialect.has_table(connection, 'users'):
                users_table.drop(engine)
                print(f"✅ Table 'users' dropped successfully.")
    except Exception as e:
        print(f"❌ An error occurred while checking for existing tables: {e}")
    finally:
        # Ensure the engine is disposed to close all connections
        if engine:
            engine.dispose()

    try:
        # If the database file already exists, remove it for a clean start
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"✅ Existing database file '{db_file}' removed.")

        # Create all tables defined in the metadata
        metadata.create_all(engine)
        print(f"✅ Tables 'users' and 'posts' created successfully in database file '{db_file}'.")
    except Exception as e:
        print(f"❌ An error occurred while setting up the database: {e}")
    finally:
        # Ensure the engine is disposed to close all connections
        if engine:
            engine.dispose()

def teardown_database(db_url: str, db_file: str):
    """Teardown Database.
    This function will remove the database file.
    """
    try:
        # If the database file exists, remove it
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"✅ Database file '{db_file}' removed successfully.")
        else:
            print(f"ℹ️ Database file '{db_file}' not found, no action needed.")
    except Exception as e:
        print(f"❌ An error occurred while tearing down the database: {e}")

if __name__ == "__main__":
    setup_database(DATABASE_URL, DB_FILE_NAME)
    # Uncomment the line below to tear down the database after testing
    # teardown_database(DATABASE_URL, DB_FILE_NAME)

```

### Key Changes for SQLite

#### 1. Simplified Configuration ⚙️

The most significant change is the database connection setup. Since SQLite is a **file-based** database, it doesn't require a running server, username, or password.

- **Original (PostgreSQL):** The connection URL used a complex string `postgresql+psycopg://user:password@host:port/dbname` to connect to a remote server.
    
- **New (SQLite):** The `DATABASE_URL` is now a simple string, `"sqlite:///my_sqlite_db.db"`. This tells SQLAlchemy to use the SQLite dialect and create a database file named `my_sqlite_db.db` in the same directory where the script is executed.
    
I also removed the `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` variables, as they are no longer necessary, due to SQLite's simplicity.

#### 2. Clean Start with File Management 📁

For a file-based database like SQLite, the "teardown" process is as simple as deleting the file itself. 

- The `setup_database` function now includes an `os.remove(db_file)` call to delete the database file if it already exists. This ensures that every time the script is run, it starts with a fresh, empty database.
    
- The `teardown_database` function is simplified to just check for and remove the database file, providing a clean way to remove all traces of the database.
    

### What Remains the Same?

The core strength of SQLAlchemy's Core is what **doesn't change**.

- **Schema Definition**: The `MetaData` object, along with the `Table` and `Column` definitions for `users_table` and `posts_table`, are **exactly the same**. SQLAlchemy's **database-agnostic** nature handles the translation of these Python objects into the correct SQL syntax for both PostgreSQL and SQLite. For example, it knows how to handle `autoincrement=True` for both database systems, even though they use different underlying mechanisms.
    
- **Engine Creation**: The function `create_engine()` is still the entry point for connectivity.
    
- **`metadata.create_all()`**: This function continues to be the primary method for generating and executing the `CREATE TABLE` statements.
    
This demonstrates how a good ORM library like SQLAlchemy allows us the developers to write highly portable database code. We can define our schema once and, with a simple change to the connection string, deploy it on a completely different database backend.
