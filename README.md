# Introduction to ORM tools with SQLAlchemy

When building applications and APIs, database integration is a key part of the process. Its a little inconvenient to use direct SQL queries to work with databases, while writing the business logic with Python or any other language. There is where Object Relational Mappers come into play. While checkout out available popular ORM libraries for python I came across SQLAlchemy, and as usual wanted to see how it works. This is a note of what I learnt. 

## What is SQLAlchemy?

When working with databases using python, we often need a way to translate your python code into SQL queries and vice versa. This is where SQL toolkits and Object Relational Mappers (ORM) comes in. 

+ **SQL Toolkits**: Provide a programmatic way to construct SQL queries using python objects, offering an abstraction layer over raw SQL strings while maintaining full control over the SQL generated. SQLAlchemy Core is an example. 

+ **Object Relational Mappers (ORM)**: Go a step further by mapping database tables to python classes and rows into python objects. This allows developers to interact with the datbase using familiar object-oriented paradigms, reducing the need to write SQL. SQLAlmechemy ORM is an example. 

## Why use SQLAlchemy?

SQLAlchemy is a comprehensive and highly regarded SQL toolkit and ORM for Python. Its key benefits include:

- **Abstraction and Database Independence:** SQLAlchemy provides a consistent API for interacting with various database systems (SQLite, PostgreSQL, MySQL, Oracle, SQL Server, etc.). This means you can often switch database backends with minimal code changes.
- **Power of SQL:** Unlike some ORMs that can hide too much SQL, SQLAlchemy is designed to expose the full power and flexibility of SQL when you need it, while providing convenient abstractions when you don't.
- **Performance:** SQLAlchemy is optimized for performance, allowing fine-grained control over query execution and data loading.
- **Flexibility:** You can choose to work at a lower level with SQLAlchemy Core (SQL expression language) or at a higher level with SQLAlchemy ORM (object mapping), or even mix and match.
- **Active Community and Rich Documentation:** A mature project with excellent support.

## Setting up the environment. 

I am going to try to show example code by using both `SQLite` database as well as `PostgreSQL`. Therefore, we need to have the following python packages installed as of now. 

```bash
# Installing sqlalchemy and postgres packages
python -m pip install sqlalchemy psycopg psycopg_binary
```
I am going to use a docker container setup for this lab. Below is the docker setup. 

```yaml
version: '3.8'

services:
  postgres_sqlalchemy:
    image: postgres:17.5
    container_name: postgres_sqlalchemy
    restart: unless-stopped
    environment:
      POSTGRES_DB: my_sqlalchemy_db
      POSTGRES_USER: sqlalchemy
      POSTGRES_PASSWORD: sqlalchemy_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - sqlalchemy

networks:
  sqlalchemy:
    driver: bridge

volumes:
  postgres_data:
    driver: local
```

Let me bring the postgres db up. 

```bash
# Building and starting the containers
docker compose up -d
# Verify whether its running
docker compose ps
```

## Connecting to Postgres with SQLAlchemy

Let me now show you a quick example of how we can connect to a Postgres databse server and perform some quick operations. 

```python
#!/usr/bin/env python3
"""
Test script to verify connection to PostgreSQL container using SQLAlchemy
"""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "my_sqlalchemy_db"
DB_USER = "sqlalchemy"
DB_PASSWORD = "sqlalchemy_password"

# Create connection string (using psycopg3)
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def test_connection():
    """Test the database connection and perform basic operations"""
    try:
        print("🔌 Testing PostgreSQL connection...")
        print(f"Database URL: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")

        # Create engine
        engine = create_engine(DATABASE_URL, echo=False)

        # Test connection
        with engine.connect() as connection:
            print("✅ Connection established successfully!")

            # Test basic query
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"📊 PostgreSQL Version: {version}")

            # Test database info
            result = connection.execute(text("SELECT current_database(), current_user"))
            db_info = result.fetchone()
            print(f"🗄️  Current Database: {db_info[0]}")
            print(f"👤 Current User: {db_info[1]}")

            # Test table creation and basic operations
            print("\n🧪 Testing basic SQL operations...")
            
            # Using placeholders for table name (not recommended for dynamic names, but for demonstration)
            # DDL statements like CREATE TABLE can't use bound parameters directly,
            # so we'll stick to a simple text execution for table creation.
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS test_users_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            connection.commit()
            print("✅ Test table created successfully")

            # Insert test data with a placeholder for 'name'
            test_user_name = 'Test Connection with Placeholder'
            connection.execute(
                text("INSERT INTO test_user_table (name) VALUES (:name)"),
                {"name": test_user_name}
            )
            connection.commit()
            print(f"✅ Test data '{test_user_name}' inserted successfully")

            # Query test data using a placeholder in a WHERE clause
            result = connection.execute(text("SELECT * FROM test_user_table WHERE name = :name"), {"name": test_user_name})
            rows = result.fetchall()
            print(f"✅ Retrieved {len(rows)} row(s) from test user table with name '{test_user_name}'")

            # Clean up test table (DDL statements cannot use placeholders for table names)
            connection.execute(text("DROP TABLE test_user_table"))
            connection.commit()
            print("✅ Test table cleaned up successfully")

        print("\n🎉 All tests passed! PostgreSQL connection is working perfectly.")
        return True

    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
```

### Code Break Down - `test_connection.py`

This Python script uses the **SQLAlchemy** library to test a connection to a **PostgreSQL** database. It verifies that it can connect, run basic queries, create a temporary table, insert data, and clean up afterwards.

The script is divided into two main parts: configuration and the `test_connection` function.

---

#### Configuration

* **Database Parameters**: The script begins by defining connection parameters as variables: `DB_HOST` (the server address, in this case `localhost`), `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`. These are the credentials needed to access the PostgreSQL database.
* **Connection String**: It then constructs a **database URL** `(DATABASE_URL)` using a formatted string. This URL follows a standard format (`dialect+driver://user:password@host:port/database`) and is what SQLAlchemy uses to establish a connection. The `postgresql+psycopg` part specifies that it's connecting to a PostgreSQL database using the `psycopg` driver, which is a popular adapter for Python. I have used the `psycopg` version 3 which is the latest. 

#### The `test_connection` Function

The core logic resides within the `test_connection` function, which is wrapped in a `try...except` block to handle potential errors gracefully.

* **Engine Creation**: It first creates a **database engine** using `create_engine(DATABASE_URL)`. An engine is a central object in SQLAlchemy that acts as a factory for connections to the database.
* **Connection and Querying**: The script then uses a `with engine.connect() as connection:` block. This ensures that the connection is automatically closed when the block is exited, even if errors occur.
    * **Version Check**: It executes a simple query `SELECT version()` to confirm the connection is active and to retrieve the PostgreSQL version.
    * **Database Info**: It runs another query `SELECT current_database(), current_user` to get the name of the database and the connected user.
    * **SQL Operations**: It tests more complex SQL operations, all enclosed within `connection.execute(text("..."))`. The `text()` function explicitly marks the query string as a literal SQL statement.
        * **Table Creation**: It creates a temporary table named `test_table` if it doesn't already exist.
        * **Data Insertion**: It inserts a row of data into the new table.
        * **Data Retrieval**: It queries the table to retrieve the inserted row(s), confirming the data was successfully added.
        * **Cleanup**: Finally, it **drops** the `test_table` to clean up the database and leave it in its original state. The `connection.commit()` calls after each operation are crucial for saving changes to the database.
* **Error Handling**: The `except` blocks catch specific `SQLAlchemyError` and general `Exception` types, printing an informative error message if anything goes wrong during the process.

The script concludes by calling `test_connection()` and using `sys.exit()` to return an exit code of `0` for success or `1` for failure, a common practice in command-line scripts.

#### SQLAlchemy `text()` function and why we use it

The primary benefit of using SQLAlchemy's `text()` function is to **explicitly mark a string as a raw SQL statement**. This provides several advantages, including security and flexibility.

-----

**Security and SQL Injection Prevention**

The `text()` function helps prevent **SQL injection attacks**. I have used placeholders with `text()` wherever possible as, SQLAlchemy's core strength is its ability to safely handle parameters. When you execute a query using `text()` with bind parameters, SQLAlchemy handles the escaping and quoting of the data for you.

For example, a safe way to insert data would be:

```python
# Insert test data with a placeholder for 'name'
test_user_name = 'Test Connection with Placeholder'
    connection.execute(
        text("INSERT INTO test_user_table (name) VALUES (:name)"),
            {"name": test_user_name}
    )
# Query test data using a placeholder in a WHERE clause
result = connection.execute(text("SELECT * FROM test_user_table WHERE name = :name"), {"name": test_user_name})
```

In this case, SQLAlchemy would correctly handle the value, preventing the malicious code from being executed. Without `text()`, concatenating strings to build a query would be highly vulnerable to such attacks.

-----

**Flexibility and Legacy Support**

`text()` allows you to execute **any valid SQL statement**, including database-specific functions or complex queries that might be difficult to construct using SQLAlchemy's higher-level ORM or core expression language. This is particularly useful for:

  * **Complex Queries**: Executing intricate joins, subqueries, or procedural logic that are easier to write directly in SQL.
  * **Legacy Databases**: Interacting with existing schemas or stored procedures without needing to fully map them to SQLAlchemy models.
  * **Performance Optimization**: Writing optimized, hand-tuned SQL for critical parts of an application.

In essence, `text()` provides a bridge between SQLAlchemy's sophisticated abstraction layer and the raw power of your database's native SQL. It allows you to selectively drop down to pure SQL when needed, while still benefiting from SQLAlchemy's connection pooling, transaction management, and other core features.

## Connecting to SQLite with SQLAlchemy

Now, I am using the same logic to do the same operations with SQLite. Difference is some of the SQL statements used in SQLite will be different to what I used in the Postgres version, because the two databases are different. 

```python
#!/usr/bin/env python3
"""
Test script to verify connection to a SQLite database using SQLAlchemy
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Database connection parameters
DB_FILE = "my_sqlalchemy_sqlite.db"

# Create connection string for SQLite
DATABASE_URL = f"sqlite:///{DB_FILE}"

def test_sqlite_connection():
    """Test the database connection and perform basic operations"""
    try:
        print("🔌 Testing SQLite connection...")
        print(f"Database URL: {DATABASE_URL}")

        # Create engine
        engine = create_engine(DATABASE_URL, echo=False)

        # Test connection
        with engine.connect() as connection:
            print("✅ Connection established successfully!")

            # Test basic query for version (SQLite specific)
            result = connection.execute(text("SELECT sqlite_version()"))
            version = result.fetchone()[0]
            print(f"📊 SQLite Version: {version}")

            # Test database info (SQLite specific)
            # SQLite doesn't have current_user, but we can get the database file path
            result = connection.execute(text("PRAGMA database_list;"))
            db_info = result.fetchone()
            # db_info will be a tuple like (0, 'main', '/path/to/my_sqlalchemy_sqlite.db')
            print(f"🗄️  Database File: {db_info[2]}")

            # Test table creation and basic operations
            print("\n🧪 Testing basic SQL operations...")

            # Create a test table (using SQLite compatible syntax for autoincrement)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS test_user_table (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            connection.commit()
            print("✅ Test table created successfully")

            # Insert test data
            test_user_name = 'Test Connection with Placeholder'
            # Using a placeholder for the name
            connection.execute(
                text("INSERT INTO test_user_table (name) VALUES (:name)"), 
                {"name": test_user_name}
            )
            
            connection.commit()
            print("✅ Test data inserted successfully")

            # Query test data
            result = connection.execute(
                text("SELECT * FROM test_user_table WHERE name = :name"),
                {"name": test_user_name}
            )

            rows = result.fetchall()
            print(f"✅ Retrieved {len(rows)} row(s) from test table")

            # Clean up test table
            connection.execute(text("DROP TABLE test_user_table"))
            connection.commit()
            print("✅ Test table cleaned up successfully")

        print("\n🎉 All tests passed! SQLite connection is working perfectly.")
        return True

    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        # Clean up the database file after the test
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            print(f"🧹 Cleaned up database file: {DB_FILE}")

if __name__ == "__main__":
    success = test_sqlite_connection()
    sys.exit(0 if success else 1)
```

### Code Break Down - `test_sqlite_connection.py`
 
#### Key Differences from the PostgreSQL Script

1. **Database Connection**: Instead of connecting to a remote server, the script connects to a local file.
    
    - `DB_FILE = "my_sqlalchemy_sqlite.db"`: This variable defines the name of the database file that will be created and used.
        
    - `DATABASE_URL = f"sqlite:///{DB_FILE}"`: The connection string is much simpler. `sqlite:///` tells SQLAlchemy to connect to a file-based SQLite database. The triple slash `///` indicates a relative path from the current directory.
        
2. **Specific SQL Commands**: SQLite has its own set of SQL functions and syntax which differs from PostgreSQL.
    
    - `SELECT sqlite_version()`: This is the SQLite-specific command to retrieve the database version.
        
    - `PRAGMA database_list;`: The script uses this SQLite command to get information about the connected database, which in this case is the file path. SQLite does not have the concept of a `current_user` and `current_database` like PostgreSQL.
        
    - `id INTEGER PRIMARY KEY AUTOINCREMENT`: The syntax for defining an auto-incrementing primary key is `AUTOINCREMENT` in SQLite, as opposed to `SERIAL` in PostgreSQL.
        
3. **Cleanup**: The script includes a `finally` block to ensure that the database file is deleted after the test is completed, regardless of whether the test was successful or not.
    
    - `if os.path.exists(DB_FILE): os.remove(DB_FILE)`: This code uses the `os` module to check if the database file exists and, if so, deletes it. This is crucial for cleanup, as SQLite is file-based and the file would otherwise persist.



## Digging into SQLAlchemy

+ [Getting Started with SQLAlchemy Core](./01-getting-started-with-sqlalchemy-core/01-getting-started-with-sqlalchemy-core.md)