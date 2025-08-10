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