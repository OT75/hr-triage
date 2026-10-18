import json
from pathlib import Path

from app.llm import extract

CASES_FILE = Path(__file__).parent / "cases.jsonl"
RESULTS_FILE = Path(__file__).parent / "results.json"


def load_cases():
    with CASES_FILE.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def evaluate(case):
    """Run one case through extraction and compare with the expected labels."""
    extraction = extract(case["text"])
    if extraction is None:
        return {**case, "predicted": "FAILED", "predicted_extra": [],
                "confidence": None, "category_ok": False, "multi_ok": False}

    predicted_extra = sorted(
        t.value for t in extraction.other_topics if t != extraction.category
    )
    return {
        **case,
        "predicted": extraction.category.value,
        "predicted_extra": predicted_extra,
        "confidence": extraction.confidence,
        "category_ok": extraction.category.value == case["category"],
        "multi_ok": bool(predicted_extra) == bool(case["other_topics"]),
    }


def per_category(results):
    """Precision and recall for each expected category."""
    categories = sorted({r["category"] for r in results})
    print("\nCategory      precision  recall")
    for c in categories:
        predicted_c = [r for r in results if r["predicted"] == c]
        expected_c = [r for r in results if r["category"] == c]
        hits = [r for r in expected_c if r["predicted"] == c]
        precision = len(hits) / len(predicted_c) if predicted_c else 0
        recall = len(hits) / len(expected_c)
        print(f"{c:<13} {precision:>8.0%}  {recall:>6.0%}")


def confidence_check(results):
    """Is confidence lower when the model is wrong? Decides the 0.7 rule."""
    right = [r["confidence"] for r in results if r["category_ok"] and r["confidence"] is not None]
    wrong = [r["confidence"] for r in results if not r["category_ok"] and r["confidence"] is not None]
    print("\nAverage confidence")
    print(f"  when right: {sum(right) / len(right):.2f}" if right else "  when right: -")
    print(f"  when wrong: {sum(wrong) / len(wrong):.2f}" if wrong else "  when wrong: - (no mistakes)")


def main():
    cases = load_cases()
    results = []
    for case in cases:
        print(f"Case {case['id']}...", end=" ", flush=True)
        results.append(evaluate(case))
        print("ok")

    total = len(results)
    category_correct = sum(r["category_ok"] for r in results)
    multi_correct = sum(r["multi_ok"] for r in results)

    print(f"\nCategory accuracy:       {category_correct}/{total} ({category_correct / total:.0%})")
    print(f"Multi-topic detection:   {multi_correct}/{total} ({multi_correct / total:.0%})")
    per_category(results)
    confidence_check(results)

    print("\nMisses:")
    for r in results:
        if not r["category_ok"] or not r["multi_ok"]:
            print(f"  #{r['id']} [{r['note']}] expected {r['category']} {r['other_topics']}, "
                  f"got {r['predicted']} {r['predicted_extra']} (conf {r['confidence']})")
            print(f"     {r['text'][:80]}")

    RESULTS_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved details to {RESULTS_FILE.name}")


if __name__ == "__main__":
    main()