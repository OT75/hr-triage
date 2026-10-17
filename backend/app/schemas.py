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
    other_topics: list[Category] = Field(
        description="Other categories this request ALSO asks about. Empty list if only one topic."
    )

class RoutingDecision(BaseModel):
    """Where a ticket goes and why. Decided by code, not by the LLM."""

    queue: str
    needs_review: bool
    reasons: list[str]

class TicketOut(BaseModel):
    """What the API returns after a request is submitted."""

    id: int
    extraction: Extraction | None
    routing: RoutingDecision
    draft: str

class DraftResult(BaseModel):
    """What the LLM returns when drafting a reply."""

    reply: str = Field(description="The reply email to the employee")
    fully_answered: bool = Field(
        description="True only if the policy answers every question in the request"
    )