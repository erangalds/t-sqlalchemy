import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, text 
from sqlalchemy.sql import insert, select, update, delete 
from sqlalchemy.exc import IntegrityError 

## Configuration for Database Connection 
# SQLite uses a file-based database.
# The 'my_sqlalchemy_db.db' file will be created in the same directory as the script.
DATABASE_URL = "sqlite:///my_sqlalchemy_db.db"


# --- Database Schema Definition ---
metadata = MetaData()

accounts_table = Table(
    "accounts", metadata,
    Column("id",  Integer, primary_key=True, autoincrement=True),
    Column("account_number", String(50), nullable=False, unique=True),
    Column("balance", Integer, nullable=False, default=0),
)

# -- Helper function for setup and data retrieval -----
def setup_accounts_table(engine):
    """Create the accounts table if it doesn't exists."""
    print("Setting up the accounts table...")
    
    with engine.connect() as connection:
        # Check if table exists and drop it if it does
        if connection.dialect.has_table(connection, "accounts"):
            # SQLite does not support CASCADE, so we simply drop the table.
            connection.execute(text("DROP TABLE accounts"))
            print("Existing accounts table dropped.")
        connection.commit()
        
        # Create the new table
        metadata.create_all(engine)
        print("Accounts table created successfully.")

    # Insert Initial Data
    with engine.connect() as connection:
        initial_data = [
            {"account_number": "ACC001", "balance": 1000},
            {"account_number": "ACC002", "balance": 2000},
            {"account_number": "ACC003", "balance": 3000},
        ] 
        connection.execute(insert(accounts_table), initial_data)
        connection.commit()
        print("Initial data inserted into accounts tabale.")

def get_account_balances(engine):
    """Retrieve account balances.""" 
    print("Current account balances:")
    with engine.connect() as connection:
        accounts_balance = select(accounts_table).order_by(accounts_table.c.account_number)

        for row in connection.execute(accounts_balance):
            print(f"Account Number: {row.account_number}, Balance: {row.balance}")

# --- Transaction Example: Fund Transfer ---
def transfer_funds(engine, from_acc_number: str, to_acc_number: str, amount: int, should_fail: bool = False):
    """Transfer funds from one account to another.""" 
    print(f"Transferring {amount} from {from_acc_number} to {to_acc_number}")

    with engine.connect() as connection:
        # Declare `trans` before the try block so it's accessible everywhere
        trans = None
        try:
            # Begin a transaction
            trans = connection.begin()
            print("Transaction Started.")

            # 1. Deduct from sender's account
            deduct_query = update(accounts_table).where(accounts_table.c.account_number == from_acc_number).values(balance=accounts_table.c.balance - amount)
            deduct_results = connection.execute(deduct_query)
            if deduct_results.rowcount == 0:
                raise ValueError(f"Account {from_acc_number} not found")
            
            # Simulate a failure if should_fail is True
            if should_fail:
                print("Simulating a failure...") 
                connection.execute(insert(accounts_table).values(account_number="ACC999", balance=1000))
                raise Exception("Simulated failure during fund transfer.")
            
            # 2. Add to destination account
            add_query = update(accounts_table).where(accounts_table.c.account_number == to_acc_number).values(balance=accounts_table.c.balance + amount)
            add_results = connection.execute(add_query)
            if add_results.rowcount == 0:
                print(f"Account {to_acc_number} not found, rolling back transaction.")
                raise ValueError(f"Account {to_acc_number} not found")
            
            # If both operations succeed, commit the transaction
            trans.commit()
            print("Transaction Committed successfully.")
        except (IntegrityError, ValueError, Exception) as e:
            # Rollback the transaction in case of any error
            print(f"Error Occurred: {e}, rolling back transaction.")
            if trans:  # Check if a transaction was actually started
                trans.rollback()
            print("Transaction Rolled back.")
        finally:
            # Display the current account balances
            get_account_balances(engine)


if __name__ == "__main__":
    try:
        # Create a database engine
        engine = create_engine(DATABASE_URL)
        print("Database connection engine created.")

        # Set up the database table and data
        setup_accounts_table(engine)
        print("---")
        get_account_balances(engine)
        print("---")

        # Example 1: Successful transfer
        transfer_funds(engine, from_acc_number="ACC001", to_acc_number="ACC002", amount=100)
        print("---")

        # Example 2: Failed transfer due to simulated error
        transfer_funds(engine, from_acc_number="ACC001", to_acc_number="ACC003", amount=50, should_fail=True)
        print("---")

        # Example 3: Transfer with non-existent account
        transfer_funds(engine, from_acc_number="NON_EXISTENT_ACC", to_acc_number="ACC002", amount=100)
        print("---")

    except Exception as e:
        print(f"An error occurred: {e}")
