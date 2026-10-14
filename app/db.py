import psycopg2
from psycopg2 import sql

from app import config


def get_connection():
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.READONLY_DB_USER,
        password=config.READONLY_DB_PASSWORD,
    )
    # Extra safety layer: this session cannot write anything
    conn.set_session(readonly=True)
    return conn


def run_query(query: str, max_rows: int = 100):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SET statement_timeout = 10000")  # stop queries running over 10 seconds
        cur.execute(query)
        columns = [d[0] for d in cur.description]
        rows = cur.fetchmany(max_rows)
        return columns, rows
    finally:
        conn.close()


def get_schema_text(max_distinct: int = 15) -> str:
    """Read tables, columns, keys and allowed text values straight from PostgreSQL."""
    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            """
        )
        columns = cur.fetchall()

        cur.execute(
            """
            SELECT c.conrelid::regclass::text, a.attname
            FROM pg_constraint c
            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
            WHERE c.contype = 'p' AND c.connamespace = 'public'::regnamespace
            """
        )
        primary_keys = {(t, col) for t, col in cur.fetchall()}

        cur.execute(
            """
            SELECT c.conrelid::regclass::text, a.attname,
                   c.confrelid::regclass::text, af.attname
            FROM pg_constraint c
            JOIN pg_attribute a  ON a.attrelid  = c.conrelid  AND a.attnum  = ANY(c.conkey)
            JOIN pg_attribute af ON af.attrelid = c.confrelid AND af.attnum = ANY(c.confkey)
            WHERE c.contype = 'f' AND c.connamespace = 'public'::regnamespace
            """
        )
        foreign_keys = {(t, col): (rt, rc) for t, col, rt, rc in cur.fetchall()}

        lines = []
        current_table = None
        for table, column, data_type in columns:
            if table != current_table:
                lines.append(f"\nTable: {table}")
                current_table = table

            note = ""
            if (table, column) in primary_keys:
                note = " [primary key]"
            elif (table, column) in foreign_keys:
                ref_table, ref_col = foreign_keys[(table, column)]
                note = f" [foreign key -> {ref_table}.{ref_col}]"

            values_note = ""
            if data_type in ("character varying", "text"):
                cur.execute(
                    sql.SQL(
                        "SELECT DISTINCT {col} FROM {tbl} "
                        "WHERE {col} IS NOT NULL ORDER BY {col} LIMIT %s"
                    ).format(col=sql.Identifier(column), tbl=sql.Identifier(table)),
                    (max_distinct + 1,),
                )
                values = [r[0] for r in cur.fetchall()]
                if len(values) <= max_distinct:
                    values_note = " (possible values: " + ", ".join(f"'{v}'" for v in values) + ")"

            lines.append(f"  - {column}: {data_type}{note}{values_note}")

        return "\n".join(lines).strip()
    finally:
        conn.close()

def get_table_names() -> list[str]:
    """Names of all real tables in the public schema (used by the SQL guard)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()