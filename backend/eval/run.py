import json
import sys
import time
from pathlib import Path

from app.config import settings
from app.llm import extract

CASES_FILE = Path(__file__).parent / "cases.jsonl"

# USD per 1 million tokens: (input, output). Check OpenAI's pricing page and update.
PRICES = {
    "gpt-5.4-mini": (0.75, 4.50),
    "gpt-5.4-nano": (0.20, 1.25),
}


def load_cases():
    with CASES_FILE.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def evaluate(case, model):
    """Run one case, timing it and counting tokens."""
    usage = {"input": 0, "output": 0}
    start = time.perf_counter()
    extraction = extract(case["text"], model=model, usage=usage)
    seconds = time.perf_counter() - start

    base = {**case, "seconds": seconds,
            "input_tokens": usage["input"], "output_tokens": usage["output"]}
    if extraction is None:
        return {**base, "predicted": "FAILED", "predicted_extra": [],
                "confidence": None, "category_ok": False, "multi_ok": False}

    predicted_extra = sorted(
        t.value for t in extraction.other_topics if t != extraction.category
    )
    return {
        **base,
        "predicted": extraction.category.value,
        "predicted_extra": predicted_extra,
        "confidence": extraction.confidence,
        "category_ok": extraction.category.value == case["category"],
        "multi_ok": bool(predicted_extra) == bool(case["other_topics"]),
    }


def per_category(results):
    categories = sorted({r["category"] for r in results})
    print("\nCategory      precision  recall")
    for c in categories:
        predicted_c = [r for r in results if r["predicted"] == c]
        expected_c = [r for r in results if r["category"] == c]
        hits = [r for r in expected_c if r["predicted"] == c]
        precision = len(hits) / len(predicted_c) if predicted_c else 0
        recall = len(hits) / len(expected_c)
        print(f"{c:<13} {precision:>8.0%}  {recall:>6.0%}")


def speed_and_cost(results, model):
    times = sorted(r["seconds"] for r in results)
    average = sum(times) / len(times)
    p95 = times[int(0.95 * (len(times) - 1))]
    print(f"\nLatency per request:  average {average:.2f}s, p95 {p95:.2f}s")

    avg_in = sum(r["input_tokens"] for r in results) / len(results)
    avg_out = sum(r["output_tokens"] for r in results) / len(results)
    print(f"Tokens per request:   {avg_in:.0f} input, {avg_out:.0f} output")

    if model in PRICES:
        price_in, price_out = PRICES[model]
        cost_per_request = (avg_in * price_in + avg_out * price_out) / 1_000_000
        print(f"Cost:                 ${cost_per_request * 1000:.2f} per 1,000 requests (extraction only)")
    else:
        print(f"Cost:                 add '{model}' to PRICES")


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else settings.extraction_model
    print(f"Model: {model}\n")

    results = []
    for case in load_cases():
        print(f"Case {case['id']}...", end=" ", flush=True)
        results.append(evaluate(case, model))
        print("ok")

    total = len(results)
    category_correct = sum(r["category_ok"] for r in results)
    multi_correct = sum(r["multi_ok"] for r in results)
    print(f"\nCategory accuracy:       {category_correct}/{total} ({category_correct / total:.0%})")
    print(f"Multi-topic detection:   {multi_correct}/{total} ({multi_correct / total:.0%})")
    per_category(results)
    speed_and_cost(results, model)

    print("\nMisses:")
    for r in results:
        if not r["category_ok"] or not r["multi_ok"]:
            print(f"  #{r['id']} [{r['note']}] expected {r['category']} {r['other_topics']}, "
                  f"got {r['predicted']} {r['predicted_extra']}")

    results_file = Path(__file__).parent / f"results_{model}.json"
    results_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved details to {results_file.name}")


if __name__ == "__main__":
    main()