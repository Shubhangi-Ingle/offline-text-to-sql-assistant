import json
import re

import ollama

from app import config
from app.db import get_schema_text

# ---------------------------------------------------------------
# Layer 1: fast rules (no model needed)
# ---------------------------------------------------------------

# Topics the shop database has no data for: (pattern, message)
UNANSWERABLE_TOPICS = [
    (r"\b(profits?|margins?)\b",
     "The database has selling prices but no cost data, so I can't calculate profit or margin."),
    (r"\b(ratings?|reviews?|feedback)\b",
     "The database has no ratings or reviews."),
    (r"\b(employees?|salary|salaries|staff)\b",
     "The database has no employee data."),
    (r"\b(suppliers?|vendors?)\b",
     "The database has no supplier data."),
    (r"\b(weather|stock market|share price)\b",
     "That is outside the shop database."),
    (r"\b(jokes?|poems?|riddles?|lyrics)\b",
     "I only answer questions about the shop data."),
]

# Vague ranking words, and the words that make them clear
RANKING_WORDS = r"\b(top|best|worst|biggest|largest|popular|leading|most valuable)\b"
METRIC_WORDS = (
    r"\b(revenue|spent|spend|spending|sold|units|quantity|amount|money|orders?|"
    r"payments?|price|stock|count|number|value|purchases?|signed|signup|registered)\b"
)

# Vague time words
TIME_WORDS = r"\b(recent|recently|lately)\b"


def pick_ranking_options(q: str) -> list:
    if re.search(r"\bcustomers?\b|\bbuyers?\b", q):
        return ["By total amount spent (paid orders)", "By number of orders placed"]
    if re.search(r"\bproducts?\b|\bitems?\b|\bcategor(y|ies)\b", q):
        return ["By units sold", "By revenue generated"]
    if re.search(r"\bcit(y|ies)\b|\bstates?\b", q):
        return ["By number of customers", "By revenue"]
    return ["By revenue", "By number of orders"]


def check_rules(question: str):
    """Return a result dict if a rule fires, otherwise None."""
    q = question.lower()

    for pattern, message in UNANSWERABLE_TOPICS:
        if re.search(pattern, q):
            return {"status": "unanswerable", "message": message}

    ranking = re.search(RANKING_WORDS, q)
    if ranking and not re.search(METRIC_WORDS, q):
        return {
            "status": "needs_clarification",
            "clarifying_question": f"When you say '{ranking.group(1)}', how should I measure it?",
            "options": pick_ranking_options(q),
        }

    recent = re.search(TIME_WORDS, q)
    if recent and not re.search(r"\d", q):
        return {
            "status": "needs_clarification",
            "clarifying_question": f"What time period do you mean by '{recent.group(1)}'?",
            "options": ["Last 30 days", "Last 3 months", "Last 12 months"],
        }

    return None


# ---------------------------------------------------------------
# Layer 2: the model checks the question
# ---------------------------------------------------------------

TRIAGE_PROMPT = """You decide whether a question can be answered right away from a shop database.

DATABASE SCHEMA:
SCHEMA_HERE

DEFAULTS THAT ALREADY EXIST (do not ask about these):
- Revenue means money from paid payments.
- Units sold counts only delivered and shipped orders.
- Dates such as "in 2025" or "last month" are clear.
- If the question names a measure, a time period or a filter, it is clear.

Reply with ONLY a JSON object in one of these three shapes:
{"status": "clear"}
{"status": "ambiguous", "question": "<one short question for the user>", "options": ["<option 1>", "<option 2>", "<option 3>"]}
{"status": "unanswerable", "message": "<one sentence saying what data is missing>"}

Use "ambiguous" only when a missing detail would clearly change the answer and there is no sensible default.
Use "unanswerable" only when the schema has no data for the question.
When in doubt, reply {"status": "clear"}.

EXAMPLES:
Question: How many orders were placed in 2025?
{"status": "clear"}

Question: Which products are doing well?
{"status": "ambiguous", "question": "What does 'doing well' mean?", "options": ["Most units sold", "Highest revenue", "Most repeat customers"]}

Question: How many customers have a premium membership?
{"status": "unanswerable", "message": "The database has no membership data."}
"""

_triage_prompt = None


def get_triage_prompt() -> str:
    global _triage_prompt
    if _triage_prompt is None:
        _triage_prompt = TRIAGE_PROMPT.replace("SCHEMA_HERE", get_schema_text())
    return _triage_prompt


def check_with_llm(question: str):
    """Return a result dict if the model finds a problem, otherwise None."""
    try:
        response = ollama.chat(
            model=config.OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": get_triage_prompt()},
                {"role": "user", "content": f"Question: {question}"},
            ],
            format="json",
            options={"temperature": 0},
        )
        data = json.loads(response["message"]["content"])
    except Exception:
        return None  # if anything goes wrong, treat the question as clear

    status = str(data.get("status", "clear")).lower()

    if status == "ambiguous":
        question_text = str(data.get("question") or "").strip()
        options = [str(o).strip() for o in (data.get("options") or []) if str(o).strip()]
        if question_text and len(options) >= 2:
            return {
                "status": "needs_clarification",
                "clarifying_question": question_text,
                "options": options[:4],
            }

    if status == "unanswerable":
        message = str(data.get("message") or "").strip()
        if message:
            return {"status": "unanswerable", "message": message}

    return None


# ---------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------

def check_question(question: str) -> dict:
    result = check_rules(question)
    if result:
        return result

    if config.USE_LLM_TRIAGE:
        result = check_with_llm(question)
        if result:
            return result

    return {"status": "clear"}


def build_refined_question(original: str, options: list, user_reply: str) -> str:
    """Combine the original question with the user's answer to the clarification."""
    reply = user_reply.strip()
    if reply.isdigit() and 1 <= int(reply) <= len(options):
        reply = options[int(reply) - 1]
    return f"{original}\nClarification from the user: {reply}"