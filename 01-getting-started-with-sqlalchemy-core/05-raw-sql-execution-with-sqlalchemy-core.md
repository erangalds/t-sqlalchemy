# Raw SQL Execution (Textual SQL)

While SQLAlchemy Core provides a powerful expression language, there are times when you simply want to execute raw SQL. SQLAlchemy supports this using the `text()` construct. This is useful for:

- Executing complex, database-specific SQL queries or DDL statements that are hard to express with SQLAlchemy's constructs.
- Integrating with existing SQL scripts.
- Debugging or quick ad-hoc queries.

## Code Breakdown

