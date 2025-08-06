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



            

            