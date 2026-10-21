from enum import Enum

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Category(str, Enum):
    payroll = "payroll"
    leave = "leave"
    documents = "documents"
    benefits = "benefits"
    onboarding = "onboarding"
    other = "other"


# What each category means. The extraction prompt is built from this,
# so adding a category = one enum line + one definition here.
CATEGORY_DEFINITIONS = {
    Category.payroll: "salary, payslips, overtime pay, tax forms",
    Category.leave: "vacation, sick leave, parental leave, time off",
    Category.documents: "employment certificates, contract copies, reference letters",
    Category.benefits: "health insurance, pension, company perks, transport",
    Category.onboarding: (
        "only for NEW employees in their first weeks: first-day setup, "
        "access badges, initial equipment, training"
    ),
    Category.other: (
        "anything else, including IT problems of existing employees, "
        "complaints or conflicts with managers or colleagues, "
        "and requests that are not about HR"
    ),
}


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

class TicketCreated(BaseModel):
    """What the employee gets back: a receipt, nothing internal."""

    id: int
    message: str


class TicketHR(BaseModel):
    """Everything HR needs to review a ticket."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    name: str
    email: str
    text: str
    category: str | None
    urgency: str | None
    language: str | None
    summary: str | None
    confidence: float | None
    other_topics: list[str]
    queue: str
    needs_review: bool
    review_reasons: list[str]
    draft: str
    final_reply: str | None
    status: str
    edited: bool


class TicketUpdate(BaseModel):
    """What HR sends to edit and/or approve a ticket."""

    reply: str | None = None
    approve: bool = False

class StatsOut(BaseModel):
    """Business metrics for HR: is the AI actually useful?"""

    total_tickets: int
    approved_tickets: int
    review_rate: float                 # share of all tickets flagged for review
    edited_rate: float | None          # share of APPROVED tickets where HR changed the draft
    tickets_per_category: dict[str, int]