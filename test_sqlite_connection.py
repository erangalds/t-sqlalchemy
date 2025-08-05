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
