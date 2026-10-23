"""Compare two models on drafting, scored blind by a human.

Step 1 (generate):  python -m eval.drafts
    Extracts each case once with the production extraction model, then drafts
    a reply with BOTH models. Writes eval/drafts_sheet.csv with the two drafts
    as "A" and "B" in random order, and the answer key to eval/drafts_key.json.

Step 2 (you):       open drafts_sheet.csv, read each pair WITHOUT opening the key,
    and put 1 (yes) or 0 (no) in the score columns:
        grounded  only facts from the policy, nothing invented
        complete  answers every part, or says HR will follow up on that part
        language  replies in the employee's language
        sendable  HR could approve it as is, or with a tiny edit

Step 3 (score):     python -m eval.drafts score
    Opens the key and prints the totals per model.
"""

import csv
import json
import random
import sys
import time
from pathlib import Path

from app.config import settings
from app.llm import draft_reply, extract
from eval.run import PRICES, load_cases

MODELS = ["gpt-5.4-mini", "gpt-5.4-nano"]
CRITERIA = ["grounded", "complete", "language", "sendable"]
NAME = "Alex"  # the cases have no names, so every draft greets the same person

HERE = Path(__file__).parent
SHEET = HERE / "drafts_sheet.csv"
KEY = HERE / "drafts_key.json"
RAW = HERE / "drafts_raw.json"


def generate():
    random.seed(42)  # same A/B order every time you run it
    rows, key, raw = [], {}, []

    for case in load_cases():
        print(f"Case {case['id']}...", end=" ", flush=True)

        # Extract ONCE, so both models draft from exactly the same input.
        extraction = extract(case["text"])
        if extraction is None or extraction.category.value == "other":
            print("skipped (holding reply, no LLM draft)")
            continue

        drafts = {}
        for model in MODELS:
            usage = {"input": 0, "output": 0}
            start = time.perf_counter()
            result = draft_reply(NAME, case["text"], extraction, model=model, usage=usage)
            drafts[model] = result.reply
            raw.append({
                "id": case["id"], "model": model, "reply": result.reply,
                "fully_answered": result.fully_answered,
                "seconds": round(time.perf_counter() - start, 2), **usage,
            })

        order = MODELS[:]
        random.shuffle(order)  # hide which model is A and which is B
        key[case["id"]] = {"A": order[0], "B": order[1]}
        rows.append({
            "id": case["id"],
            "request": case["text"],
            "category": extraction.category.value,
            "language": extraction.language,
            "draft_A": drafts[order[0]],
            "draft_B": drafts[order[1]],
            **{f"A_{c}": "" for c in CRITERIA},
            **{f"B_{c}": "" for c in CRITERIA},
        })
        print("ok")

    with SHEET.open("w", newline="", encoding="utf-8-sig") as f:  # -sig: Excel shows umlauts correctly
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    KEY.write_text(json.dumps(key, indent=2), encoding="utf-8")
    RAW.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{len(rows)} cases drafted by both models.")
    print(f"Score {SHEET.name} blind, then run: python -m eval.drafts score")
    cost_summary(raw)


def cost_summary(raw):
    print("\nModel           avg latency   cost per 1,000 drafts")
    for model in MODELS:
        runs = [r for r in raw if r["model"] == model]
        seconds = sum(r["seconds"] for r in runs) / len(runs)
        price_in, price_out = PRICES[model]
        cost = sum(r["input"] * price_in + r["output"] * price_out for r in runs) / len(runs) / 1_000_000
        print(f"{model:<15} {seconds:>8.2f}s   ${cost * 1000:.2f}")


def score():
    key = json.loads(KEY.read_text(encoding="utf-8"))
    with SHEET.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    totals = {m: {c: 0 for c in CRITERIA} for m in MODELS}
    for row in rows:
        for side in ("A", "B"):
            model = key[row["id"]][side]
            for c in CRITERIA:
                value = row[f"{side}_{c}"].strip()
                if value not in ("0", "1"):
                    sys.exit(f"Case {row['id']}, {side}_{c}: expected 0 or 1, got '{value}'")
                totals[model][c] += int(value)

    n = len(rows)
    print(f"{n} cases\n")
    print(f"{'':<15}" + "".join(f"{c:>11}" for c in CRITERIA))
    for model in MODELS:
        print(f"{model:<15}" + "".join(f"{totals[model][c]:>8}/{n}" for c in CRITERIA))

    print("\nWhere they differ:")
    for row in rows:
        a, b = key[row["id"]]["A"], key[row["id"]]["B"]
        diff = [c for c in CRITERIA if row[f"A_{c}"].strip() != row[f"B_{c}"].strip()]
        if diff:
            better = {c: (a if row[f"A_{c}"].strip() == "1" else b) for c in diff}
            print(f"  #{row['id']}: " + ", ".join(f"{c} -> {m}" for c, m in better.items()))


if __name__ == "__main__":
    score() if sys.argv[1:] == ["score"] else generate()