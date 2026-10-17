import pytest
from pydantic import ValidationError

from app.schemas import Category, Extraction, RequestIn


def valid_extraction():
    return {
        "category": "leave",
        "urgency": "low",
        "language": "en",
        "summary": "Wants 3 days off in May",
        "confidence": 0.9,
    }


def test_valid_extraction():
    e = Extraction(**valid_extraction()) # Unpacks Dict into keywords arguments
    assert e.category == Category.leave


def test_confidence_above_one_is_rejected():
    data = valid_extraction() | {"confidence": 1.5} # Merge (right value wins, so new conf for object = 1.5)
    with pytest.raises(ValidationError):
        Extraction(**data)


def test_unknown_category_is_rejected():
    data = valid_extraction() | {"category": "parking"}
    with pytest.raises(ValidationError):
        Extraction(**data)


def test_bad_email_is_rejected():
    with pytest.raises(ValidationError):
        RequestIn(name="Omar", email="not-an-email", text="I need my payslip")