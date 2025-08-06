# Raw SQL Execution (Textual SQL)

While SQLAlchemy Core provides a powerful expression language, there are times when you simply want to execute raw SQL. SQLAlchemy supports this using the `text()` construct. This is useful for:

- Executing complex, database-specific SQL queries or DDL statements that are hard to express with SQLAlchemy's constructs.
- Integrating with existing SQL scripts.
- Debugging or quick ad-hoc queries.

## Code Breakdown

### Postgres Implementation

```python 
import os
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String 

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

raw_data_table = Table(
    "raw_data", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("value", String(50), )
)

# Defining a function to execute raw SQL
def perform_raw_sql_operations(db_url: str):
    """Executes raw SQL Operations on the database."""
    print(f"Performing raw SQL operations on {db_url}...") 
    # Create an engine
    engine = create_engine(db_url, echo=True)

    try:
        # Connect to the database
        with engine.connect() as connection:
            # DROP Table if it exists
            connection.execute(text("DROP TABLE IF EXISTS raw_data"))
            # Creaet Table
            connection.execute(text(
                    """
                    CREATE TABLE raw_data(
                        id SERIAL PRIMARY KEY,
                        value VARCHAR(50)
                    )"""
                )
            )
            print("✅ Table 'raw_data' created successfully.")
            # Insert data using raw SQL
            # Parameter binding to prevent SQL injection
            insert_sql = text("INSERT INTO raw_data (value) VALUES (:value)")
            # Execute the insert statements 
            connection.execute(insert_sql, {"value": "data value 1"})
            connection.execute(insert_sql, {"value": "data value 2"})
            connection.commit() # save the changes 
            print("✅ Data inserted successfully.") 

            # Querying data using raw SQL
            select_sql = text("SELECT id, value FROM raw_data WHERE value LIKE :pattern")
            result = connection.execute(select_sql, {"pattern": "data%"})
            print("✅ Query Results:")
            for row in result:
                print(f"ID: {row.id}, value: {row.value}")
            
            # update data using raw SQL
            update_sql = text("UPDATE raw_data SET value = :new_value WHERE id = :id")
            connection.execute(update_sql, {"new_value": "updated value", "id": 1})
            connection.commit()
            print("✅ Data updated successfully.")

            # Verify the udpate
            result = connection.execute(select_sql, {"pattern": "updated%"})
            print("✅ Updated Query Results:")
            for row in result:
                print(f"ID: {row.id}, value: {row.value}")
            
            # Delete data using raw SQL
            delete_sql = text("DELETE FROM raw_data WHERE id = :id_to_delete")
            connection.execute(delete_sql, {"id_to_delete": 2})
            connection.commit()
            print("✅ Data deleted successfully.")

            # Verify the deletion
            result = connection.execute(text("SELECT * FROM raw_data"))
            print("✅ Final Query Results:")
            for row in result:
                print(f"ID: {row.id}, value: {row.value}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the engine
        engine.dispose()
        print("✅ Database connection closed.")
    

if __name__ == "__main__":
    # perform raw SQL operations
    perform_raw_sql_operations(DATABASE_URL)

```

#### 1. Database Configuration ⚙️

```python
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "my_sqlalchemy_db"
DB_USER = "sqlalchemy"
DB_PASSWORD = "sqlalchemy_password"

DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
```

This section defines the parameters needed to connect to a PostgreSQL database.

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: These variables hold the credentials and location of our PostgreSQL database.
    
- `DATABASE_URL`: This f-string constructs the connection string for SQLAlchemy. `postgresql+psycopg://`specifies that it's a PostgreSQL database and uses the `psycopg` driver (which is `psycopg3` in modern SQLAlchemy versions) to connect.
    

---

#### 2. Database Schema Definition 📊


```python
metadata = MetaData()

raw_data_table = Table(
    "raw_data", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("value", String(50), )
)
```

Although this script primarily focuses on raw SQL, it still defines a SQLAlchemy `Table` object.

- `metadata = MetaData()`: An instance of `MetaData` is a container that holds information about your database schema (tables, columns, constraints, etc.).
    
- `raw_data_table = Table(...)`: This defines a table named `"raw_data"`.
    
    - `Column("id", Integer, primary_key=True, autoincrement=True)`: This creates an `id` column as an integer, sets it as the **primary key**, and enables **auto-incrementing** (meaning the database will automatically assign a unique, sequential number to `id` for each new row).
        
    - `Column("value", String(50))`: This creates a `value` column that can store strings up to 50 characters long.
        

**Note**: While this `Table` object is defined, the script explicitly uses raw SQL `CREATE TABLE` statements, which means this `Table` object isn't directly used to create the table in the database in this specific example. It's more for conceptual schema representation here.

---

#### 3. `perform_raw_sql_operations` Function 🛠️

This is the main function that encapsulates all the database interactions.

##### Creating the Engine and Connection 🚀


```python
def perform_raw_sql_operations(db_url: str):
    print(f"Performing raw SQL operations on {db_url}...") 
    engine = create_engine(db_url, echo=True)

    try:
        with engine.connect() as connection:
            # ... operations ...
```

- `engine = create_engine(db_url, echo=True)`:
    
    - `create_engine` establishes the connection to the database using the provided `db_url`.
        
    - `echo=True` is very useful for debugging and learning; it instructs SQLAlchemy to **print all SQL statements** it executes to the console.
        
- `with engine.connect() as connection:`: This creates a **database connection** and ensures it's properly closed when the `with` block is exited (even if errors occur). This is a best practice for managing database resources.
    

##### Table Management (Raw SQL) 🗑️➕

```python
            connection.execute(text("DROP TABLE IF EXISTS raw_data"))
            connection.execute(text(
                    """
                    CREATE TABLE raw_data(
                        id SERIAL PRIMARY KEY,
                        value VARCHAR(50)
                    )"""
                )
            )
            print("✅ Table 'raw_data' created successfully.")
```

- `text("...")`: This is crucial for executing raw SQL. SQLAlchemy's `text()` construct allows you to wrap a plain SQL string, making it executable by the engine.
    
- `connection.execute(...)`: This method sends the SQL command to the database.
    
- `DROP TABLE IF EXISTS raw_data`: This SQL command safely deletes the `raw_data` table if it already exists, ensuring a clean slate for each run.
    
- `CREATE TABLE raw_data(...)`: This SQL command creates the `raw_data` table. Notice `id SERIAL PRIMARY KEY`, which is the PostgreSQL-specific way to define an auto-incrementing primary key.
    

##### Inserting Data 📤


```python
            insert_sql = text("INSERT INTO raw_data (value) VALUES (:value)")
            connection.execute(insert_sql, {"value": "data value 1"})
            connection.execute(insert_sql, {"value": "data value 2"})
            connection.commit() # save the changes 
            print("✅ Data inserted successfully.") 
```

- `insert_sql = text("INSERT INTO raw_data (value) VALUES (:value)")`: This defines an `INSERT`statement. The `:value` is a **parameter placeholder**.
    
- `connection.execute(insert_sql, {"value": "data value 1"})`: When executing, you pass a dictionary (or a list of dictionaries for multiple rows) where keys match the parameter placeholders. This mechanism is called **parameter binding** and is vital for preventing **SQL injection vulnerabilities**.
    
- `connection.commit()`: After modifying the database (inserting, updating, deleting), you must call `commit()` to **save the changes permanently**. Without it, changes would be rolled back when the connection closes.
    

##### Querying Data 🔎

```python
            select_sql = text("SELECT id, value FROM raw_data WHERE value LIKE :pattern")
            result = connection.execute(select_sql, {"pattern": "data%"})
            print("✅ Query Results:")
            for row in result:
                print(f"ID: {row.id}, value: {row.value}")
```

- `select_sql = text("SELECT id, value FROM raw_data WHERE value LIKE :pattern")`: Defines a `SELECT`statement with a `LIKE` clause and a parameter placeholder `:pattern`.
    
- `result = connection.execute(select_sql, {"pattern": "data%"})`: Executes the query, binding `"data%"`to the `:pattern` placeholder (which means "starts with 'data'").
    
- `for row in result:`: The `execute` method returns a `Result` object, which is iterable. Each `row` in the result can be accessed by attribute (e.g., `row.id`, `row.value`).
    

##### Updating Data ✏️

```python
            update_sql = text("UPDATE raw_data SET value = :new_value WHERE id = :id")
            connection.execute(update_sql, {"new_value": "updated value", "id": 1})
            connection.commit()
            print("✅ Data updated successfully.")
            # ... Verification ...
```

- `update_sql = text("UPDATE raw_data SET value = :new_value WHERE id = :id")`: Defines an `UPDATE`statement with two parameter placeholders.
    
- `connection.execute(update_sql, {"new_value": "updated value", "id": 1})`: Updates the `value` of the row where `id` is 1.
    
- `connection.commit()`: Saves the update.
    

##### Deleting Data ❌

```python
            delete_sql = text("DELETE FROM raw_data WHERE id = :id_to_delete")
            connection.execute(delete_sql, {"id_to_delete": 2})
            connection.commit()
            print("✅ Data deleted successfully.")
            # ... Verification ...
```

- `delete_sql = text("DELETE FROM raw_data WHERE id = :id_to_delete")`: Defines a `DELETE` statement with a parameter placeholder.
    
- `connection.execute(delete_sql, {"id_to_delete": 2})`: Deletes the row where `id` is 2.
    
- `connection.commit()`: Saves the deletion.
    

##### Error Handling and Cleanup 🧹

```python
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        engine.dispose()
        print("✅ Database connection closed.")
```

- `try...except Exception as e:`: This block catches any general exceptions that might occur during database operations, printing an error message.
    
- `finally:`: This block is guaranteed to execute whether an exception occurred or not.
    
- `engine.dispose()`: This is important for **releasing all connections** held by the engine in its connection pool. It ensures that database resources are properly cleaned up.
    

---

### SQLite Implementation

```python
import os
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String 

## Configuration for Database Connection 
# SQLite uses a file-based database.
# The 'my_sqlalchemy_db.db' file will be created in the same directory as the script.
DATABASE_URL = "sqlite:///my_sqlalchemy_db.db" # Changed for SQLite


# --- Database Schema Definition ---
# This metadata is primarily for SQLAlchemy's ORM or declarative base,
# but in this script, we are using raw SQL for table creation and operations.
# It's kept for consistency and potential future ORM integration.
metadata = MetaData()

raw_data_table = Table(
    "raw_data", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True), # autoincrement=True is handled by SQLAlchemy for SQLite
    Column("value", String(50), )
)

# Defining a function to execute raw SQL
def perform_raw_sql_operations(db_url: str):
    """Executes raw SQL Operations on the database."""
    print(f"Performing raw SQL operations on {db_url}...") 
    # Create an engine
    # echo=True will print all SQL statements executed to the console
    engine = create_engine(db_url, echo=True)

    try:
        # Connect to the database using a context manager, ensuring proper closing
        with engine.connect() as connection:
            # DROP Table if it exists
            # SQLite does not support 'CASCADE', so it's removed.
            connection.execute(text("DROP TABLE IF EXISTS raw_data"))
            print("✅ Existing table 'raw_data' dropped (if it existed).")

            # Create Table using raw SQL
            # For SQLite, 'INTEGER PRIMARY KEY' implicitly handles auto-increment.
            # 'AUTOINCREMENT' can be explicitly added but is often not necessary.
            connection.execute(text(
                    """
                    CREATE TABLE raw_data(
                        id INTEGER PRIMARY KEY, -- Changed from SERIAL for SQLite
                        value VARCHAR(50)
                    )"""
                )
            )
            print("✅ Table 'raw_data' created successfully.")

            # Insert data using raw SQL
            # Parameter binding is used to prevent SQL injection vulnerabilities.
            insert_sql = text("INSERT INTO raw_data (value) VALUES (:value)")
            # Execute the insert statements with bound parameters
            connection.execute(insert_sql, {"value": "data value 1"})
            connection.execute(insert_sql, {"value": "data value 2"})
            connection.commit() # Commit the transaction to save the changes
            print("✅ Data inserted successfully.") 

            # Querying data using raw SQL
            select_sql = text("SELECT id, value FROM raw_data WHERE value LIKE :pattern")
            result = connection.execute(select_sql, {"pattern": "data%"})
            print("✅ Query Results:")
            for row in result:
                # Access columns by attribute name (e.g., row.id, row.value)
                print(f"ID: {row.id}, value: {row.value}")
            
            # Update data using raw SQL
            update_sql = text("UPDATE raw_data SET value = :new_value WHERE id = :id")
            connection.execute(update_sql, {"new_value": "updated value", "id": 1})
            connection.commit() # Commit the update
            print("✅ Data updated successfully.")

            # Verify the update
            result = connection.execute(select_sql, {"pattern": "updated%"})
            print("✅ Updated Query Results:")
            for row in result:
                print(f"ID: {row.id}, value: {row.value}")
            
            # Delete data using raw SQL
            delete_sql = text("DELETE FROM raw_data WHERE id = :id_to_delete")
            connection.execute(delete_sql, {"id_to_delete": 2})
            connection.commit() # Commit the deletion
            print("✅ Data deleted successfully.")

            # Verify the deletion
            result = connection.execute(text("SELECT * FROM raw_data"))
            print("✅ Final Query Results:")
            for row in result:
                print(f"ID: {row.id}, value: {row.value}")

    except Exception as e:
        # Catch and print any errors that occur during the operations
        print(f"An error occurred: {e}")
    finally:
        # Ensure the database engine and its connections are properly disposed of
        engine.dispose()
        print("✅ Database connection closed.")
    

if __name__ == "__main__":
    # Execute the raw SQL operations function
    perform_raw_sql_operations(DATABASE_URL)

```

### Key Changes for SQLite 🛠️

1. **`DATABASE_URL`**:
    
    - The connection string is changed to `"sqlite:///my_sqlalchemy_db.db"`. This tells SQLAlchemy to use the SQLite dialect and connect to a file-based database named `my_sqlalchemy_db.db`. If the file doesn't exist, SQLite will create it.
        
2. **`CREATE TABLE` Statement**:
    
    - The `id` column definition in the `CREATE TABLE` raw SQL string is changed from `SERIAL PRIMARY KEY` to `INTEGER PRIMARY KEY`.
        
    - In SQLite, when a column is declared as `INTEGER PRIMARY KEY`, it automatically becomes an **alias for `ROWID`**and handles auto-incrementing behavior. You can optionally add `AUTOINCREMENT` (e.g., `id INTEGER PRIMARY KEY AUTOINCREMENT`), but it's generally not needed unless you specifically require that `ROWID` values are strictly increasing and never reused (even after deletions), which has performance implications. For most cases, `INTEGER PRIMARY KEY` is sufficient.
        

All other parts of the script, including the `text()` construct for raw SQL, parameter binding, `connection.execute()`, and `connection.commit()`, remain the same because SQLAlchemy provides a consistent interface across different database backends.