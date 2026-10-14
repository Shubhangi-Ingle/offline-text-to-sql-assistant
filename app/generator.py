import re

import ollama

from app import config
from app.db import get_schema_text
from app.prompt import build_system_prompt

_system_prompt = None


def get_system_prompt() -> str:
    # Read the schema once and reuse it for every question
    global _system_prompt
    if _system_prompt is None:
        _system_prompt = build_system_prompt(get_schema_text())
    return _system_prompt


def clean_sql(text: str) -> str:
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1)
    return text.strip()


def generate_sql(question: str) -> str:
    response = ollama.chat(
        model=config.OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": question},
        ],
        options={"temperature": 0, "num_ctx": 4096},
    )
    return clean_sql(response["message"]["content"])

def fix_sql(question: str, bad_sql: str, error: str) -> str:
    """Show the model its own failed query and the error, and ask for a fix."""
    response = ollama.chat(
        model=config.OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": question},
            {"role": "assistant", "content": bad_sql},
            {
                "role": "user",
                "content": (
                    f"That query failed with this error:\n{error}\n\n"
                    "Fix the query. Use only the tables and columns listed in the schema. "
                    "Return only the corrected SQL query."
                ),
            },
        ],
        options={"temperature": 0, "num_ctx": 4096},
    )
    return clean_sql(response["message"]["content"])