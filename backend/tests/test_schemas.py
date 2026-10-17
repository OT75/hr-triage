import pytest 

# python -m pytest
# It finds all subfolders of the directory its been called from
# And it finds all files with "test_" in name and checks all functions starting with "test_" in file. And test files must be in a folder named "tests"

# python -m pytest -v                          # show each test name
# python -m pytest tests\test_schemas.py       # run one file
# python -m pytest -k email                    # only tests with "email" in the name
# python -m pytest -x                          # stop at the first failure

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