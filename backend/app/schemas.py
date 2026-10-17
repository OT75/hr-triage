from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class Category(str, Enum):
    payroll = "payroll"
    leave = "leave"
    documents = "documents"
    benefits = "benefits"
    onboarding = "onboarding"
    other = "other"


class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RequestIn(BaseModel):
    """What an employee submits through the form."""

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    text: str = Field(min_length=5, max_length=5000)


class Extraction(BaseModel):
    """What the LLM must return for every request."""

    category: Category = Field(description="The HR topic of the request")
    urgency: Urgency = Field(description="How time-sensitive the request is")
    language: str = Field(
        min_length=2, max_length=2,
        description="Two-letter language code of the request, e.g. 'en' or 'de'",
    )
    summary: str = Field(max_length=300, description="One-sentence summary in English")
    confidence: float = Field(
        ge=0, le=1, description="How sure the model is about the category, 0 to 1"
    )


class TicketOut(BaseModel):
    """What the API returns after a request is submitted."""

    id: int
    extraction: Extraction | None
    needs_review: bool