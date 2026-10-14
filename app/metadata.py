import re

from app.db import get_connection, get_table_names

NOTE = "Answered directly from the database catalog, no model needed"
OVERVIEW_PATTERNS = [
    r"(what is|what's|describe|explain|tell me about|give me an overview of) (this|the|our) (database|schema|data)( about)?",
    r"what (is|does) (this|the|our) (database|data) (about|contain|have|include)",
    r"what('s| is) in (this|the|our) (database|data)",
    r"what data (do we have|is there|is available|do you have)",
    r"what can i ask",
]

def _run(query: str, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        columns = [d[0] for d in cur.description]
        return columns, cur.fetchall()
    finally:
        conn.close()


def _result(question: str, shown_sql: str, columns: list, rows: list) -> dict:
    return {
        "question": question,
        "sql": shown_sql,
        "status": "ok",
        "message": None,
        "note": NOTE,
        "columns": columns,
        "rows": rows,
        "attempts": [],
    }


def _find_table(q: str, tables: list):
    """Return the table name mentioned in the question, if any."""
    for table in tables:
        names = {table}
        if table.endswith("s"):
            names.add(table[:-1])
        for name in names:
            if re.search(rf"\b{re.escape(name)}\b", q):
                return table
    return None


def answer_metadata_question(question: str):
    """Answer questions about the database structure. Return None for anything else."""
    q = question.lower().strip().rstrip("?.! ")

    # Overview questions such as "what is this database about"
    if any(re.fullmatch(pattern, q) for pattern in OVERVIEW_PATTERNS):
        sql = ("SELECT table_name, COUNT(*) AS column_count FROM information_schema.columns "
               "WHERE table_schema = 'public' GROUP BY table_name ORDER BY table_name")
        columns, rows = _run(sql)
        return _result(question, sql, columns, rows)

    asks_columns = re.search(r"\b(columns?|fields?)\b", q)
    asks_tables = re.search(r"\btables\b", q)
    if not (asks_columns or asks_tables):
        return None
    
    tables = get_table_names()
    table = _find_table(q, tables)
    wants_list = re.search(r"\b(list|show|what|which|name|give|display|tell)\b", q)

    # How many columns (in one table, or in the whole database)
    if re.search(r"\bhow many (columns|fields)\b", q):
        if table:
            sql = ("SELECT COUNT(*) AS column_count FROM information_schema.columns "
                   f"WHERE table_schema = 'public' AND table_name = '{table}'")
            columns, rows = _run(
                "SELECT COUNT(*) AS column_count FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = %s",
                (table,),
            )
        else:
            sql = ("SELECT COUNT(*) AS total_columns FROM information_schema.columns "
                   "WHERE table_schema = 'public'")
            columns, rows = _run(sql)
        return _result(question, sql, columns, rows)

    # How many tables
    if re.search(r"\bhow many tables\b", q):
        sql = ("SELECT COUNT(*) AS total_tables FROM information_schema.tables "
               "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
        columns, rows = _run(sql)
        return _result(question, sql, columns, rows)

    # Columns of one table
    if asks_columns and table and wants_list:
        sql = ("SELECT column_name, data_type FROM information_schema.columns "
               f"WHERE table_schema = 'public' AND table_name = '{table}' "
               "ORDER BY ordinal_position")
        columns, rows = _run(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position",
            (table,),
        )
        return _result(question, sql, columns, rows)

    # All columns of the whole database
    if asks_columns and wants_list:
        sql = ("SELECT table_name, column_name, data_type FROM information_schema.columns "
               "WHERE table_schema = 'public' ORDER BY table_name, ordinal_position")
        columns, rows = _run(sql)
        return _result(question, sql, columns, rows)

    # List the tables
    if asks_tables and wants_list:
        sql = ("SELECT table_name, COUNT(*) AS column_count FROM information_schema.columns "
               "WHERE table_schema = 'public' GROUP BY table_name ORDER BY table_name")
        columns, rows = _run(sql)
        return _result(question, sql, columns, rows)

    return None