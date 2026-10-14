import re


def check_result(question: str, sql: str, columns: list, rows: list):
    """Look at the finished result with common sense.
    Return a message describing the problem, or None if the result looks fine."""
    # Only look at the first line, because refined questions have a clarification added below it
    main_question = question.strip().splitlines()[0].lower()
    sql_lower = sql.lower()

    # Check 1: a "how many" question must produce exactly ONE row with the number
    is_how_many = re.match(r"\s*how many\b", main_question)
    asks_for_groups = re.search(r"\b(each|per|every|by)\b", main_question)
    if is_how_many and not asks_for_groups and len(rows) != 1:
        return (
            f"Wrong result shape: the query returned {len(rows)} rows, but a 'how many' question "
            "needs exactly ONE row with one number. If you group by customer or product, put the "
            "grouping inside a subquery and count it: "
            "SELECT COUNT(*) FROM (SELECT ... GROUP BY ... HAVING ...) t. "
            "Do not use INTERSECT, UNION or EXCEPT between counts."
        )

    # Check 2: revenue must only count paid payments
    if (
        "revenue" in main_question
        and "payments" in sql_lower
        and "payment_status" not in sql_lower
    ):
        return (
            "Wrong business rule: revenue means money actually received, so the query must only "
            "count paid payments. Add the condition payment_status = 'paid'."
        )

    return None