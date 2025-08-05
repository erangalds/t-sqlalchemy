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
    
