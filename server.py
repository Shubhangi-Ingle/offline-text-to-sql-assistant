import json
import os
import time
import traceback
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import config
from app.clarify import build_refined_question
from app.db import get_schema_text
from app.pipeline import handle_question

app = FastAPI(title="Offline Text-to-SQL Assistant")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join("static", "index.html"))

LOG_PATH = os.path.join("logs", "queries.jsonl")
MAX_QUESTION_LENGTH = 500

EXAMPLE_QUESTIONS = [
    "How many customers are from Pune?",
    "Which category has the highest revenue?",
    "Show me our top customers",
    "How many orders were cancelled in 2025?",
    "What is the total revenue from UPI payments?",
    "Which state has the most customers?",
]


class AskRequest(BaseModel):
    question: str


class ClarifyRequest(BaseModel):
    question: str          # the original question
    reply: str             # the user's answer: an option number or their own words
    options: list[str] = []


def log_query(result: dict, seconds: float):
    """Append one line per question. Result rows are NOT logged."""
    os.makedirs("logs", exist_ok=True)
    entry = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "model": config.OLLAMA_MODEL,
        "question": result.get("question"),
        "status": result.get("status"),
        "sql": result.get("sql"),
        "note": result.get("note"),
        "attempts": len(result.get("attempts", [])),
        "seconds": round(seconds, 1),
        "message": result.get("message"),
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def build_response(result: dict, seconds: float) -> dict:
    response = {
        "status": result.get("status"),
        "question": result.get("question"),
        "sql": result.get("sql"),
        "message": result.get("message"),
        "clarifying_question": result.get("clarifying_question"),
        "options": result.get("options"),
        "columns": result.get("columns", []),
        "rows": result.get("rows", []),
        "attempts": len(result.get("attempts", [])),
        "seconds": round(seconds, 1),
        "model": config.OLLAMA_MODEL,
    }
    # Converts Decimal, date and tuple values into JSON-friendly types
    return jsonable_encoder(response)


def run(question: str, skip_check: bool) -> dict:
    start = time.time()
    try:
        result = handle_question(question, skip_check=skip_check)
    except Exception as e:
        traceback.print_exc()  # the full error still shows in the terminal for debugging
        result = {
            "question": question,
            "status": "error",
            "sql": None,
            "message": f"Unexpected error: {type(e).__name__}",
            "attempts": [],
        }
    seconds = time.time() - start
    log_query(result, seconds)
    return build_response(result, seconds)

@app.get("/api/health")
def health():
    return {"status": "ok", "model": config.OLLAMA_MODEL}


@app.get("/api/examples")
def examples():
    return {"examples": EXAMPLE_QUESTIONS}


@app.get("/api/schema")
def schema():
    return {"schema": get_schema_text()}


@app.post("/api/ask")
def ask(req: AskRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please type a question.")
    if len(question) > MAX_QUESTION_LENGTH:
        raise HTTPException(status_code=400, detail="The question is too long.")
    return run(question, skip_check=False)


@app.post("/api/clarify")
def clarify(req: ClarifyRequest):
    original = req.question.strip()
    reply = req.reply.strip()
    if not original or not reply:
        raise HTTPException(status_code=400, detail="Question and reply are required.")
    if len(original) > MAX_QUESTION_LENGTH or len(reply) > MAX_QUESTION_LENGTH:
        raise HTTPException(status_code=400, detail="The text is too long.")

    refined = build_refined_question(original, req.options, reply)
    data = run(refined, skip_check=True)
    data["question"] = original  # show the user's own question, not the combined one
    return data