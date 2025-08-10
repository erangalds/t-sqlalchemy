# Handling Transaction for Multiple Operations with SQLAlchemy ORM

Just like with Core, ORM operations also take place within transactions. It's crucial to manage these transactions when multiple database operations must succeed or fail together as an atomic unit. The `Session` object itself manages the transaction lifecycle.

**Ensuring Atomicity:** The `with Session() as session:` block implicitly handles a transaction. If no unhandled exceptions occur, `session.commit()` is called when the block exits. If an exception _is_ raised, `session.rollback()` is automatically called.

**Using `try...except...finally` blocks with `session.commit()` and `session.rollback()`:** While the `with`statement is generally preferred, explicit `try...except...finally` blocks can be used for more fine-grained control, especially if you need to perform actions _after_ a rollback, or if you're not using a context manager pattern.

## Code Breakdown

### Postgres Implementation

```python


```

#### How it Works

The code is structured around several key components:

- **Imports and Configuration:** It imports necessary libraries from `sqlalchemy`, defines database connection parameters, and creates a **`DATABASE_URL`** string to connect to a PostgreSQL database using the `psycopg` driver.
    
- **Declarative Base and Model:** The `Base` class serves as the foundation for all ORM models. The `Account` class inherits from `Base` and defines the structure of the **`accounts`** table, including columns for `id`, `account_number`, and `balance`. The `Mapped` type hints are a modern SQLAlchemy feature that maps Python types to database columns.
    
- **`setup_accounts_orm_table(engine)`:** This function sets up the database table. It first drops the `accounts` table if it exists and then creates it based on the `Account` model definition. It also populates the table with three initial account records. A `sessionmaker` is used to create a session factory, which is a key component for interacting with the database. The **`session.add_all()`** and **`session.commit()`**methods are used to stage and save the initial data.
    
- **`get_account_balances_orm(engine)`:** This function demonstrates a basic data retrieval operation. It creates a session, executes a query to fetch all account records, and prints their details. The **`session.query()`** method is a fundamental way to build queries in SQLAlchemy's classic style.
    
- **`transfer_funds_orm(engine, ...)`:** This is the core function demonstrating a database transaction. The function ensures that either all changes are successfully saved or none are.
    
    - **Acquiring a Lock:** The `.with_for_update()` method is crucial here. It acquires a pessimistic lock on the selected rows (**`from_account`** and **`to_account`**), preventing other transactions from modifying them until the current transaction is completed. This is essential to prevent race conditions during the fund transfer.
        
    - **Transaction Logic:** It retrieves the source and destination accounts, checks for sufficient funds, and updates the balances.
        
    - **Simulated Failure:** The `if should_fail:` block simulates an error condition by attempting to add a duplicate account number (`ACC001`), which will violate the **`unique=True`** constraint on the `account_number` column.
        
    - **Exception Handling:** The `try...except...finally` block is vital for transaction safety. If an error occurs (like `ValueError` for insufficient funds or `IntegrityError` for a database constraint violation), the **`session.rollback()`** method is called. This reverts all changes made within the current session, ensuring the database remains in a consistent state. If everything succeeds, **`session.commit()`**saves the changes permanently.
        

---

#### Main Execution Flow

The `if __name__ == "__main__":` block orchestrates the script's execution:

1. **`engine = create_engine(...)`**: It creates the database engine, which manages connections to the database. The `echo=True` parameter tells SQLAlchemy to print the SQL statements it executes, which is useful for debugging.
    
2. **`setup_accounts_orm_table(engine)`**: The initial table is set up and populated.
    
3. **`get_account_balances_orm(engine)`**: The initial balances are printed.
    
4. **`transfer_funds_orm(...)`**: Three different fund transfer scenarios are executed:
    
    - A **successful transfer** from ACC001 to ACC002.
        
    - A **failed transfer** from ACC001 to ACC003 due to the simulated `IntegrityError`. The rollback ensures that no balance changes are saved.
        
    - A **failed transfer** from a nonexistent account, which triggers a `ValueError` and a rollback.
        
5. **`engine.dispose()`**: The database engine is disposed of, closing all connections.


### SQLite Implementation

```python
import os
from sqlalchemy import create_engine, String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.exc import IntegrityError, NoResultFound, MultipleResultsFound

## Configuration for Database Connection
# SQLite database file path
DB_FILE = "my_sqlite_database.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"

# Defining the Declarative Base Class
class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""
    pass

# Defining the Accounts Model
class Account(Base):
    """ORM Model for Account Table."""
    __tablename__ = "accounts" # Maps this class to Accounts table
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    balance: Mapped[float] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"Account(id={self.id!r}, account_number={self.account_number!r}, balance={self.balance!r})"

# Helper function to setup and data retrieval
def setup_accounts_orm_table(engine):
    """Setting up the Accounts Table"""
    print(f'\nSetting up Accounts table in {engine.name} (ORM)\n')
    # Droping the table if exists
    Base.metadata.drop_all(engine)
    # Creating the Accounts table
    Base.metadata.create_all(engine)
    print(f'Created Accounts table in {engine.name} (ORM)')

    # Setting up a Session
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)

    # Inserting the Data
    with Session() as session:
        initial_data = [
            Account(account_number='ACC001', balance=1000),
            Account(account_number='ACC002', balance=500),
            Account(account_number='ACC003', balance=200),
        ]
        session.add_all(initial_data) # marking the data records to be added
        session.commit() # Saving the data records into the database
        print(f'\nInital Accounts Data Inserted Successfully...\n')


# Defining a function to get account balances
def get_account_balances_orm(engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)
    with Session() as session:
        print(f'\n--------------------- Current Account Balances---------------------------\n')
        # Using session.query for simple queries
        accounts = session.query(Account).order_by(Account.account_number).all()
        for account in accounts:
            print(f'Account Number: {account.account_number}, Balance: {account.balance}')

# Working on the Transactions : Transfer Funds (ORM)
def transfer_funds_orm(engine, from_account_number: str, to_account_number: str, amount: int, should_fail: bool = False):
    """Function to transfer funds between two accounts"""
    print(f'\nAttempting to Transfer Funds from {from_account_number} to {to_account_number}, Fail?: {should_fail}\n')

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)
    with Session() as session:
        try:
            # 1. Retrieve Source Account
            from_account = session.query(Account).filter_by(account_number=from_account_number).with_for_update(nowait=True).first()
            if not from_account:
                raise ValueError(f'Source Account {from_account_number} not fount')

            if from_account.balance < amount:
                raise ValueError(f'Insufficient Funds in Account {from_account_number}')

            # 2. Retrieve Destination Account
            to_account = session.query(Account).filter_by(account_number=to_account_number).with_for_update(nowait=True).first()
            if not to_account:
                raise ValueError(f'Destination Account {to_account_number} not found')

            # 3. Deduct from Source and add to Desination Accounts
            from_account.balance -= amount
            to_account.balance += amount

            # Simulate an error condition if should_faile is Trure
            if should_fail:
                print(f'Simulating an error in fund transfer.....')
                # Adding a duplicate record
                session.add(Account(account_number='ACC001', balance=999))

            # Commit the changes
            session.commit()
            print(f'Fund Transfer from {from_account_number} to {to_account_number} successful.')
        except (ValueError, IntegrityError) as e:
            print(f'Fund Transfer Failed. Rolling back transaction. Error {e}')
            session.rollback()
        except Exception as e:
            print(f'An unexpected error occurred: {e}')
            session.rollback()
        finally:
            get_account_balances_orm(engine)


# Main Execution Block
if __name__ == "__main__":
    # Create the database engine
    engine = create_engine(DATABASE_URL, echo=True)
    setup_accounts_orm_table(engine)
    get_account_balances_orm(engine)

    transfer_funds_orm(engine, "ACC001", "ACC002", 200, should_fail=False) # Successful transfer
    transfer_funds_orm(engine, "ACC001", "ACC003", 500, should_fail=True)  # Failed transfer (simulated unique constraint violation)
    transfer_funds_orm(engine, "NONEXISTENT", "ACC001", 100) # Failed transfer (source not found)

    engine.dispose()
    print("\n--- SQLite ORM transactions complete. ---")
```

#### How it works

1. **`DATABASE_URL`**: The database connection string has been changed from a PostgreSQL format to a SQLite format.
    
    - **Original:** `f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"`
        
    - **New:** `f"sqlite:///{DB_FILE}"`

    This new format tells SQLAlchemy to use the SQLite driver and creates a file named `my_sqlite_database.db` in the same directory as the script. If you want to use an in-memory database, you would use `"sqlite:///:memory:"`.
    
2. **`transfer_funds_orm` function**: SQLite's support for row-level locking is limited and handled differently than in PostgreSQL. The `with_for_update()` method in SQLAlchemy works with SQLite, but it performs a **table-level lock**, not a row-level lock. I've added `nowait=True` to the `with_for_update()` call, which is a good practice to avoid deadlocks, though its behavior can vary between database backends. For single-threaded applications like this script, the transaction itself ensures atomicity, and the lock is more for demonstrating the concept.
    
    - **Original:** `session.query(Account).filter_by(...).with_for_update().first()`
        
    - **New:** `session.query(Account).filter_by(...).with_for_update(nowait=True).first()`
        
3. **No `psycopg` driver**: The change from PostgreSQL to SQLite means you no longer need the `psycopg` driver or the specific database connection parameters like host, port, user, and password. SQLite is a file-based database, so all you need is the path to the database file.