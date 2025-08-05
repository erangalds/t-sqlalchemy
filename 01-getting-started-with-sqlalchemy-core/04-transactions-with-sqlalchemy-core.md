# Transactions (SQLAlchemy Core Expression Language)

While we've used `connection.commit()` implicitly in the `with engine.connect() as connection:` block (which starts a transaction and commits it on successful exit), it's crucial to understand explicit transaction control, especially for operations that involve multiple steps that must succeed or fail as a single atomic unit.

**Key Concepts:**

- **Atomicity:** All operations within a transaction either complete successfully (commit) or none of them do (rollback). This prevents partial updates and maintains data integrity.
- **`Connection.begin()`:** Explicitly starts a new transaction.
- **`Connection.commit()`:** Saves all changes made within the current transaction to the database.
- **`Connection.rollback()`:** Undoes all changes made within the current transaction.


## Code Breakdown 

### Postgres Implementation

```python
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, text 
from sqlalchemy.sql import insert, select, update, delete 
from sqlalchemy.exc import IntegrityError 

## Configuration for Database Connection 
# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "my_sqlalchemy_db"
DB_USER = "sqlalchemy"
DB_PASSWORD = "sqlalchemy_password"

# Create connection string (using psycopg3)
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


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
        if connection.dialect.has_table(connection, "accounts"):
            connection.execute(text("DROP TABLE accounts CASCADE"))
            print("Existing accounts table dropped.")
        # Commit the changes
        connection.commit()
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

```

#### **Code Structure and Setup**

The script is logically divided into three main sections:

1. **Database Configuration and Schema**: At the top, you define the connection details for a PostgreSQL database and then use `sqlalchemy.Table` to create a schema for an `accounts` table. This table has columns for a unique `account_number` and a `balance`.
    
2. **Helper Functions**:
    
    - `setup_accounts_table(engine)`: This function is responsible for preparing the database. It connects to the database, checks if the `accounts` table already exists, and drops it to start with a clean slate. It then uses `metadata.create_all(engine)` to create the new table. Finally, it populates the table with three initial accounts, each with a different balance.
        
    - `get_account_balances(engine)`: A simple utility function that connects to the database, queries all rows from the `accounts` table, and prints the current balance for each account. It's used to show the state of the database before and after a transaction.
        
3. **The Transaction Function and Execution**: The core logic is in `transfer_funds`, which is called with different parameters in the `if __name__ == "__main__"` block to demonstrate various transaction scenarios.
    

---

#### **In-Depth Look at `transfer_funds`**

This function simulates a fund transfer between two accounts, and it's where the transaction logic is implemented.

1. **Starting a Transaction**:
    
    Python
    
    ```
    trans = None
    try:
        trans = connection.begin()
        print("Transaction Started.")
    ```
    
    This is the crucial part you asked about. The variable `trans` is initialized to `None` outside the `try` block. Then, inside the `try` block, `connection.begin()` is called to explicitly start a database transaction, and the returned transaction object is assigned to `trans`. This makes `trans` accessible to the `except` and `finally` blocks, as it's no longer confined to the `try` scope.
    
2. **Database Operations**:
    
    - **Deduction**: The first step is an `UPDATE` query that subtracts the specified `amount` from the sender's account (`from_acc_number`). A check is performed to ensure the `rowcount` is not zero, meaning the account was actually found. If not, a `ValueError` is raised, which will trigger a rollback.
        
    - **Simulated Failure**: The `should_fail` parameter allows you to intentionally cause an error during the transaction by raising an `Exception`. This is a great way to test the rollback functionality.
        
    - **Addition**: The second step is another `UPDATE` query that adds the `amount` to the recipient's account (`to_acc_number`). Again, a `rowcount` check ensures the recipient account exists.
        
3. **Committing the Transaction**:
    
    Python
    
    ```
    trans.commit()
    print("Transaction Committed successfully.")
    ```
    
    If all the operations in the `try` block succeed without raising an exception, `trans.commit()` is called. This permanently saves all the changes to the database.
    
4. **Handling Errors with Rollback**:
    
    Python
    
    ```
    except (IntegrityError, ValueError, Exception) as e:
        print(f"Error Occurred: {e}, rolling back transaction.")
        if trans:
            trans.rollback()
        print("Transaction Rolled back.")
    ```
    
    If any error occurs within the `try` block, execution immediately jumps to this `except` block. Here's what happens:
    
    - The `if trans:` check is a **safety measure** to ensure a transaction was actually started before attempting to roll it back.
        
    - `trans.rollback()` is then called, which is the core of the solution. It **reverses all the changes** that were made to the database since `trans = connection.begin()` was called, returning the database to its state before the transaction began.
        
5. **Finalizing with `finally`**:
    
    Python
    
    ```
    finally:
        get_account_balances(engine)
    ```
    
    The `finally` block is executed regardless of whether the `try` block completed successfully or an exception was caught. In this case, it's used to print the account balances. This is very useful because you can see the results of a successful commit or the unchanged state of a rolled-back transaction.
    

---

#### **The Three Transaction Examples**

The `if __name__ == "__main__"` block runs three distinct scenarios to demonstrate the transaction's behavior:

1. **Successful Transfer**: `transfer_funds(..., amount=100)`. This call runs without any errors. Both the deduction and addition succeed, and `trans.commit()` is called, making the changes permanent.
    
2. **Simulated Failure**: `transfer_funds(..., amount=50, should_fail=True)`. The code first deducts 50 from `ACC001`'s balance, but then hits the `if should_fail:` condition. An `Exception` is raised, the `except` block catches it, and `trans.rollback()` is called. The balances for all accounts are reverted to their original state.
    
3. **Non-Existent Account**: `transfer_funds(..., from_acc_number="NON_EXISTENT_ACC")`. The initial `update`query for the sender account finds no matching rows, so its `rowcount` is 0. This triggers the `ValueError` you defined. The `except` block catches the error and `trans.rollback()` is called, ensuring no changes are committed to the database.


### SQLite Implementation

```python
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
```

#### Key Changes for SQLite

The conversion from PostgreSQL to SQLite primarily involves these two modifications:

- **Connection String**: The `DATABASE_URL` is changed from a complex string with host, port, user, and password to a simple file path. `sqlite:///my_sqlalchemy_db.db` tells SQLAlchemy to use the **SQLite dialect** and create a database file named `my_sqlalchemy_db.db` in the same directory as the script.
    
- **`DROP TABLE` Syntax**: SQLite does not support the `CASCADE` keyword, which is used in PostgreSQL to drop dependent objects. The code has been simplified to `connection.execute(text("DROP TABLE accounts"))`, which is sufficient for this example.
    
The rest of the code, including the `transfer_funds` function and the transaction handling logic, remains the same because **SQLAlchemy provides a consistent API** for managing transactions regardless of the underlying database.
