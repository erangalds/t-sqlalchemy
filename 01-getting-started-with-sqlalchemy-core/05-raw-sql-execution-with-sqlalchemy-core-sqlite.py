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
