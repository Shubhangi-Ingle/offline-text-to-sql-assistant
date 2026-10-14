import argparse
import json
import os
import time
from collections import Counter
from datetime import date, datetime
from decimal import Decimal

from app import config
from app.db import run_query
from app.pipeline import answer_question
from evaluation.final_set import FINAL_CASES
from evaluation.heldout_set import HELDOUT_CASES
from evaluation.test_set import TEST_CASES
# ---------- comparing results ----------

def norm_value(v):
    if v is None:
        return "None"
    if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
        return f"{round(float(v), 2):.2f}"
    if isinstance(v, (date, datetime)):
        return v.isoformat()[:10]
    return str(v).strip().lower()


def norm_row(row):
    return Counter(norm_value(v) for v in row)


def rows_match(gold_rows, generated_rows):
    """Same number of rows; every gold row's values must appear in a distinct generated row.
    Row order is ignored and extra columns in the generated rows are allowed."""
    if len(gold_rows) != len(generated_rows):
        return False
    generated = [norm_row(r) for r in generated_rows]
    used = [False] * len(generated)
    for gold_row in gold_rows:
        gold = norm_row(gold_row)
        for i, candidate in enumerate(generated):
            if not used[i] and not (gold - candidate):
                used[i] = True
                break
        else:
            return False
    return True


# ---------- summary ----------

def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "n/a"


def summarize(records):
    total = len(records)
    correct = sum(r["correct"] for r in records)
    first_try = sum(1 for r in records if r["correct"] and r["attempts"] == 1)

    by_difficulty = {}
    for level in ("easy", "medium", "hard"):
        subset = [r for r in records if r["difficulty"] == level]
        if subset:
            by_difficulty[level] = {
                "correct": sum(r["correct"] for r in subset),
                "total": len(subset),
            }

    return {
        "model": config.OLLAMA_MODEL,
        "total": total,
        "correct": correct,
        "accuracy": round(100 * correct / total, 1) if total else 0,
        "first_try_correct": first_try,
        "first_try_accuracy": round(100 * first_try / total, 1) if total else 0,
        "blocked": sum(1 for r in records if r["status"] == "blocked"),
        "errors": sum(1 for r in records if r["status"] == "error"),
        "wrong_answers": sum(1 for r in records if r["status"] == "ok" and not r["correct"]),
        "avg_seconds": round(sum(r["seconds"] for r in records) / total, 1) if total else 0,
        "by_difficulty": by_difficulty,
    }


def print_summary(records):
    s = summarize(records)
    print("\n" + "=" * 60)
    print(f"RESULTS FOR MODEL: {s['model']}")
    print("=" * 60)
    print(f"Final accuracy (with self-correction): {s['correct']}/{s['total']} = {pct(s['correct'], s['total'])}")
    print(f"First-try accuracy (no retries):       {s['first_try_correct']}/{s['total']} = {pct(s['first_try_correct'], s['total'])}")
    print("\nBy difficulty:")
    for level, d in s["by_difficulty"].items():
        print(f"  {level:<7} {d['correct']}/{d['total']} = {pct(d['correct'], d['total'])}")
    print(f"\nWrong answers (ran but wrong result): {s['wrong_answers']}")
    print(f"Failed to produce working SQL:        {s['errors']}")
    print(f"Blocked by the guard:                 {s['blocked']}")
    print(f"Average time per question:            {s['avg_seconds']} seconds")

    failed = [r["id"] for r in records if not r["correct"]]
    print(f"\nFailed question ids: {failed if failed else 'none'}")


def save_results(records, set_name="dev"):
    os.makedirs("evaluation/results", exist_ok=True)
    safe_model = config.OLLAMA_MODEL.replace(":", "_").replace("/", "_")
    path = os.path.join("evaluation", "results", f"results_{safe_model}_{set_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"set": set_name, "summary": summarize(records), "records": records},
            f,
            indent=2,
        )
    return path


# ---------- main ----------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="only run the first N questions")
    parser.add_argument("--model", default=None, help="Ollama model name to evaluate")
    parser.add_argument("--set", dest="set_name", choices=["dev", "heldout", "final"], default="dev",
                        help="which question set to run")
    args = parser.parse_args()

    if args.model:
        config.OLLAMA_MODEL = args.model

    all_cases = {"dev": TEST_CASES, "heldout": HELDOUT_CASES, "final": FINAL_CASES}[args.set_name]
    cases = all_cases[: args.limit] if args.limit else all_cases
    print(f"Evaluating model '{config.OLLAMA_MODEL}' on the {args.set_name} set ({len(cases)} questions)\n")

    records = []
    for i, case in enumerate(cases, start=1):
        _, gold_rows = run_query(case["gold_sql"])

        start = time.time()
        result = answer_question(case["question"])
        seconds = time.time() - start

        correct = result["status"] == "ok" and rows_match(gold_rows, result["rows"])

        records.append({
            "id": case["id"],
            "difficulty": case["difficulty"],
            "question": case["question"],
            "generated_sql": result["sql"],
            "status": result["status"],
            "attempts": len(result["attempts"]),
            "correct": bool(correct),
            "seconds": round(seconds, 1),
            "error": result["message"],
        })

        label = "PASS" if correct else "FAIL"
        print(f"[{i:>2}/{len(cases)}] {case['difficulty']:<6} {label}  {seconds:5.1f}s  {case['question']}")
        if not correct:
            print(f"        status: {result['status']}  attempts: {len(result['attempts'])}")
            print(f"        SQL: {result['sql']}")
            if result["message"]:
                print(f"        error: {result['message'][:150]}")

        save_results(records, args.set_name)  # saved after every question

    print_summary(records)
    print(f"\nSaved to: {save_results(records, args.set_name)}")


if __name__ == "__main__":
    main()