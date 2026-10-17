from app.schemas import Category, Extraction, RoutingDecision, Urgency

CONFIDENCE_THRESHOLD = 0.7   # measured in 3.1; kept or removed based on the results

QUEUES = {
    Category.payroll: "payroll",
    Category.leave: "time-off",
    Category.documents: "documents",
    Category.benefits: "benefits",
    Category.onboarding: "onboarding",
    Category.other: "general",
}


def route(extraction: Extraction | None) -> RoutingDecision:
    """Decide the queue and whether a human must review. Plain rules, no LLM."""
    if extraction is None:
        return RoutingDecision(
            queue="general", needs_review=True, reasons=["AI extraction failed"]
        )

    reasons = []
    if extraction.category == Category.other:
        reasons.append("no clear HR category")
    if extraction.urgency == Urgency.high:
        reasons.append("high urgency")
    if extraction.confidence < CONFIDENCE_THRESHOLD:
        reasons.append(f"low confidence ({extraction.confidence:.2f})")

    extra_topics = [t for t in extraction.other_topics if t != extraction.category]
    if extra_topics:
        names = ", ".join(t.value for t in extra_topics)
        reasons.append(f"also asks about: {names}")

    return RoutingDecision(
        queue=QUEUES[extraction.category],
        needs_review=bool(reasons),   # any reason at all → review
        reasons=reasons,
    )