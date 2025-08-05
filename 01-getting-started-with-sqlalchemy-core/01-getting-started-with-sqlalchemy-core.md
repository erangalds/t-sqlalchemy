# SQLAlchemy Core

## SQLAlchemy Core vs. SQLAlchemy ORM: Understanding the philosophical differences and when to use each.

- **SQLAlchemy Core (Schema-centric, Low-level SQL expression language):**
    - **Focus:** Directly represents database schemas (tables, columns, indexes) and allows you to construct SQL queries programmatically using Python objects.
    - **Use Cases:**
        - When you need precise control over the generated SQL.
        - Performing bulk operations (insert, update, delete).
        - Working with stored procedures or complex database-specific features.
        - Building tools that interact with databases at a lower level (e.g., migration tools, data pipelines).
        - When you prefer writing "Pythonic SQL" over ORM objects.
- **SQLAlchemy ORM (Domain-centric, Pythonic object manipulation):**
    - **Focus:** Maps Python classes to database tables and instances of those classes to rows. You interact with database data primarily through Python objects.
    - **Use Cases:**
        - Building typical CRUD applications where you manipulate individual records as objects.
        - Managing complex relationships between data entities (one-to-many, many-to-many).
        - When you want to reduce the amount of explicit SQL you write.
        - For applications where object-oriented design principles are central to your data model.

**Choosing between Core and ORM:** It's not an either/or choice. Many applications use both: Core for specific bulk operations or highly optimized queries, and ORM for general application logic and object manipulation. SQLAlchemy is designed to facilitate this synergy.

## Basic Database Operations with SQLAlchemy Core

Now, let me show you how to define database schemas and perform basic CRUD operations with SQLAlchemy Core.

+ [**Defining Schemas:**](./02-defining-schemas.md)
+ [**Performing CRUD Operations**](./0)

