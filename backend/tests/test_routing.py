from app.routing import route
from app.schemas import Category, Extraction, Urgency, CATEGORY_DEFINITIONS


def make_extraction(**changes):
    """A clear, single-topic, low-urgency request. Override fields per test."""
    data = {
        "category": Category.leave,
        "urgency": Urgency.low,
        "language": "en",
        "summary": "Wants 3 days off in May",
        "confidence": 0.95,
        "other_topics": [],
    }
    return Extraction(**(data | changes))


def test_clear_request_goes_to_its_queue_without_review():
    decision = route(make_extraction())
    assert decision.queue == "time-off"
    assert decision.needs_review is False
    assert decision.reasons == []


def test_other_category_needs_review():
    decision = route(make_extraction(category=Category.other))
    assert decision.needs_review is True
    assert decision.queue == "general"


def test_extra_topics_need_review():
    decision = route(make_extraction(other_topics=[Category.benefits]))
    assert decision.needs_review is True
    assert "also asks about: benefits" in decision.reasons


def test_main_category_repeated_in_other_topics_is_ignored():
    decision = route(make_extraction(other_topics=[Category.leave]))
    assert decision.needs_review is False


def test_high_urgency_needs_review():
    decision = route(make_extraction(urgency=Urgency.high))
    assert decision.needs_review is True
    assert "high urgency" in decision.reasons

def test_low_confidence_alone_does_not_trigger_review():
    # Eval (18 Oct): confidence didn't separate right from wrong answers,
    # so it was removed from routing on purpose.
    decision = route(make_extraction(confidence=0.4))
    assert decision.needs_review is False


def test_failed_extraction_needs_review_in_general_queue():
    decision = route(None)
    assert decision.needs_review is True
    assert decision.queue == "general"


def test_every_category_has_a_definition():
    for category in Category:
        assert category in CATEGORY_DEFINITIONS