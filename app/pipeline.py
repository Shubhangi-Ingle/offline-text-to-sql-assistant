from app.checks import check_result
from app.clarify import check_question
from app.db import get_table_names, run_query
from app.generator import fix_sql, generate_sql
from app.guard import OutOfScopeError, RetryableSQLError, UnsafeSQLError, validate_sql
from app.metadata import answer_metadata_question
MAX_RETRIES = 2

_allowed_tables = None


def get_allowed_tables():
    global _allowed_tables
    if _allowed_tables is None:
        _allowed_tables = get_table_names()
    return _allowed_tables


def answer_question(question: str, first_sql: str = None) -> dict:
    """
    Question -> model -> guard -> database -> result check,
    with up to MAX_RETRIES self-corrections.
    first_sql lets us skip the model for the first attempt (used for testing).
    """
    result = {
        "question": question,
        "sql": None,
        "status": None,   # "ok", "blocked" or "error"
        "message": None,
        "columns": [],
        "rows": [],
        "attempts": [],   # every try: the SQL and the error (if any)
    }

    sql = first_sql if first_sql is not None else generate_sql(question)
    error = None

    for attempt in range(MAX_RETRIES + 1):
        record = {"attempt": attempt + 1, "sql": sql, "error": None}
        result["attempts"].append(record)
        result["sql"] = sql

        try:
            safe_sql = validate_sql(sql, get_allowed_tables())
        except OutOfScopeError as e:
            # Not a question about the data at all, so retrying will not help
            record["error"] = str(e)
            result["status"] = "unanswerable"
            result["message"] = "That doesn't look like a question about the shop data."
            return result
        
        except UnsafeSQLError as e:
            # Unsafe request (DELETE, DROP, ...): never retry
            record["error"] = str(e)
            result["status"] = "blocked"
            result["message"] = str(e)
            return result
        else:
            try:
                columns, rows = run_query(safe_sql)
            except Exception as e:
                error = str(e).strip()
            else:
                # The query ran. Does the result make sense?
                problem = check_result(question, safe_sql, columns, rows)
                if problem is None:
                    result["sql"] = safe_sql
                    result["status"] = "ok"
                    result["columns"] = columns
                    result["rows"] = rows
                    return result
                error = problem

        record["error"] = error

        if attempt == MAX_RETRIES:
            break
        sql = fix_sql(question, sql, error)

    result["status"] = "error"
    result["message"] = error
    return result


def handle_question(question: str, skip_check: bool = False) -> dict:
    """The main entry point: structure questions, then the clarity check, then the model."""
    if not skip_check:
        metadata_result = answer_metadata_question(question)
        if metadata_result is not None:
            return metadata_result

        check = check_question(question)
        if check["status"] != "clear":
            check["question"] = question
            return check
    return answer_question(question)