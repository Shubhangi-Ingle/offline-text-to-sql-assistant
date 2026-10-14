from app.clarify import build_refined_question
from app.pipeline import handle_question


def print_answer(result: dict):
    print(f"\nSQL used:\n{result['sql']}\n")

    if result["status"] == "ok":
        if not result["rows"]:
            print("No matching rows found.")
            return
        print(" | ".join(result["columns"]))
        print("-" * 40)
        for row in result["rows"][:20]:
            print(" | ".join(str(value) for value in row))
        if len(result["rows"]) > 20:
            print(f"... and {len(result['rows']) - 20} more rows")
    elif result["status"] == "blocked":
        print("I can't run that:", result["message"])
    else:
        print("Sorry, I couldn't get a working query:", result["message"])


def main():
    print("Ask a question about the shop database (type 'exit' to quit).")

    while True:
        question = input("\nYou: ").strip()
        if not question:
            continue
        if question.lower() in ("exit", "quit"):
            break

        print("Thinking...")
        result = handle_question(question)

        if result["status"] == "unanswerable":
            print(f"\nAssistant: {result['message']}")
            print("I can answer questions about customers, products, orders and payments.")
            continue

        if result["status"] == "needs_clarification":
            print(f"\nAssistant: {result['clarifying_question']}")
            for number, option in enumerate(result["options"], start=1):
                print(f"  {number}. {option}")
            reply = input("You (type a number or your own answer): ").strip()
            if not reply:
                continue
            refined = build_refined_question(question, result["options"], reply)
            print("Thinking...")
            result = handle_question(refined, skip_check=True)

        print_answer(result)


if __name__ == "__main__":
    main()