import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError, TokenError


class UnsafeSQLError(Exception):
    """Raised when the generated SQL is not safe to run."""
class RetryableSQLError(UnsafeSQLError):
    """The SQL is broken or uses an unknown table, so the model can try to fix it."""
class OutOfScopeError(UnsafeSQLError):
    """The query reads no table, so it cannot be an answer from the database."""
# The query must start as a SELECT (or UNION / INTERSECT / EXCEPT of SELECTs)
_ALLOWED_ROOTS = (exp.Select, getattr(exp, "SetOperation", exp.Union))

# Statement types that must not appear anywhere, even hidden inside a query
_FORBIDDEN_NODE_NAMES = [
    "Insert", "Update", "Delete", "Drop", "Alter", "Create", "Command",
    "Merge", "TruncateTable", "Copy", "Grant", "Set", "Into", "Lock",
    "Transaction", "Commit", "Rollback",
]
_FORBIDDEN_NODES = tuple(
    node_type
    for node_type in (getattr(exp, name, None) for name in _FORBIDDEN_NODE_NAMES)
    if node_type is not None
)

# Functions that can freeze the server, read files or change settings
_FORBIDDEN_FUNCTIONS = {
    "pg_sleep", "pg_sleep_for", "pg_sleep_until",
    "pg_read_file", "pg_read_binary_file", "pg_ls_dir", "pg_stat_file",
    "lo_import", "lo_export", "dblink", "dblink_exec",
    "set_config", "current_setting",
    "pg_terminate_backend", "pg_cancel_backend",
}


def validate_sql(sql: str, allowed_tables) -> str:
    """Return the cleaned SQL if it is safe, otherwise raise UnsafeSQLError."""
    sql = (sql or "").strip()
    if not sql:
        raise UnsafeSQLError("The model did not return any SQL.")

    allowed = {t.lower() for t in allowed_tables}

    # 1. It must be readable SQL, and exactly one statement
    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except (ParseError, TokenError) as e:
        raise RetryableSQLError(f"This is not valid SQL: {str(e)[:150]}")

    if len(statements) != 1:
        raise UnsafeSQLError("Only one SQL statement is allowed.")
    tree = statements[0]

    # 2. It must be a SELECT query
    if not isinstance(tree, _ALLOWED_ROOTS):
        raise UnsafeSQLError("Only SELECT queries are allowed.")

    # 3. No data-changing statements hidden inside the query
    for bad in tree.find_all(*_FORBIDDEN_NODES):
        raise UnsafeSQLError(f"Forbidden operation found: {type(bad).__name__}.")

    # 4. No dangerous functions
    for func in tree.find_all(exp.Func):
        name = func.name if isinstance(func, exp.Anonymous) else func.sql_name()
        if name and name.lower() in _FORBIDDEN_FUNCTIONS:
            raise UnsafeSQLError(f"The function '{name}' is not allowed.")

    # 5. Only the shop's own tables (temporary WITH names are fine)
    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        table_name = table.name.lower()
        if not table_name:
            raise UnsafeSQLError("Table functions are not allowed.")
        if table.db and table.db.lower() != "public":
            raise UnsafeSQLError(f"Access to schema '{table.db}' is not allowed.")
        if table_name not in allowed and table_name not in cte_names:
            raise RetryableSQLError(f"Table '{table.name}' does not exist or is not allowed.")
    # 6. The query must read data from at least one table
    if not any(True for _ in tree.find_all(exp.Table)):
        raise OutOfScopeError("The query does not read any table, so it is not a question about the data.")
    return sql.rstrip(";").strip()