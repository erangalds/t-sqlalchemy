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