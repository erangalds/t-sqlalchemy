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
