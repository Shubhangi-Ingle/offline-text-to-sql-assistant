import glob
import json
import os

rows = []
for path in sorted(glob.glob("evaluation/results/results_*.json")):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    label = os.path.basename(path)[len("results_"):-len(".json")]
    rows.append((label, data["summary"]))

print(f"{'Run':<42}{'Final':>8}{'First-try':>11}{'Wrong':>7}{'Errors':>8}{'Avg sec':>9}")
print("-" * 85)
for label, s in rows:
    print(
        f"{label:<42}{s['accuracy']:>7}%{s['first_try_accuracy']:>10}%"
        f"{s['wrong_answers']:>7}{s['errors']:>8}{s['avg_seconds']:>9}"
    )