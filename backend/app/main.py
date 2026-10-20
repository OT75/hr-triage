from fastapi import Depends, FastAPI, HTTPException, Request, status
from openai import AuthenticationError, OpenAIError
from sqlalchemy.orm import Session

from sqlalchemy import func

from app import models  # noqa: F401  (imported so SQLAlchemy registers the Ticket table)
from app.db import Base, engine, get_db

from app.auth import require_hr
from app.config import settings
from app.llm import draft_reply, extract
from app.models import Ticket
from app.schemas import RequestIn, TicketCreated, TicketHR, TicketUpdate, StatsOut
from app.routing import route

import logging
import time
import uuid
from app.logging_setup import log_event, request_id_var, setup_logging

from prometheus_client import make_asgi_app

from app.metrics import ERRORS, TICKETS

from langfuse import observe

from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,   # which websites may call this API (For Development: allow_origins=["*"]), but never in a real HR system
    allow_methods=["*"],                   # GET, POST, PATCH...
    allow_headers=["*"],                   # e.g. Content-Type, Authorization
    expose_headers=["X-Request-ID"],       # let the frontend read the request ID
)

app.mount("/metrics", make_asgi_app())

setup_logging()

 
@app.middleware("http") #It’s a wrapper around every endpoint: every request passes through it on the way in and on the way out.
async def add_request_id(request: Request, call_next): # No Endpoint
    
    if request.url.path.startswith("/metrics"):
        return await call_next(request)       # don't log Prometheus' visits

    """Give every request an ID, and log how long it took."""
    request_id = uuid.uuid4().hex[:8]
    request_id_var.set(request_id)
    start = time.perf_counter()

    response = await call_next(request)         # ← The endpoint runs here
                                                # Everything before it happens first; everything after it happens once the endpoint is done

    log_event(
        "request_finished",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        ms=round((time.perf_counter() - start) * 1000),
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- Employee side ----------

@app.post("/requests", response_model=TicketCreated, status_code=status.HTTP_201_CREATED) # after the observe (Bottom up order)
@observe(name="hr_request", capture_input=False) # capture_input is false for data privacy of employees (Name, Email) records extract/draft functions outputs
def create_request(request: RequestIn, db: Session = Depends(get_db)):  # db: one session per request, closed afterwards
    try:
        extraction = extract(request.text) # 1. LLM: what is it about?
        draft = draft_reply(request.name, request.text, extraction)# 2. LLM: write a reply
    except AuthenticationError: # Wrong API Key, The message is vague on purpose: the user doesn’t need to know about our API key.
        log_event("llm_auth_failed", level=logging.ERROR)
        ERRORS.labels(step="llm_auth").inc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
    except OpenAIError: # Any other OpenAI failure (network, timeout, outage)
        log_event("llm_unavailable", level=logging.ERROR, error=type(error).__name__)
        ERRORS.labels(step="llm_unavailable").inc()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The AI service is unavailable. Please try again in a minute.")

    decision = route(extraction, draft.fully_answered) # 3. Code: where, and review?

    log_event(
        "routed",
        category=extraction.category.value if extraction else None,
        queue=decision.queue,
        needs_review=decision.needs_review,
        reasons=decision.reasons,
    )

    ticket = Ticket(                                   # 4. Save it in PostgreSQL
        name=request.name,
        email=request.email,
        text=request.text,
        category=extraction.category.value if extraction else None,
        urgency=extraction.urgency.value if extraction else None,
        language=extraction.language if extraction else None,
        summary=extraction.summary if extraction else None,
        confidence=extraction.confidence if extraction else None,
        other_topics=[t.value for t in extraction.other_topics] if extraction else [],
        queue=decision.queue,
        needs_review=decision.needs_review,
        review_reasons=decision.reasons,
        draft=draft.reply,
    )
    db.add(ticket)       # "save this", nothing sent yet
    db.commit()          # now: INSERT INTO tickets ...
    db.refresh(ticket)   # reload, so ticket.id from Postgres is filled in
    
    log_event("ticket_saved", ticket_id=ticket.id)
    TICKETS.labels(category=ticket.category or "failed").inc()

    return TicketCreated(                              # the employee only gets a receipt
        id=ticket.id,
        message="Thanks! HR has received your request and will reply by email.",
    )


# ---------- HR side (password protected) ----------

def get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


@app.get("/tickets", response_model=list[TicketHR], dependencies=[Depends(require_hr)])
def list_tickets(
    status_filter: str | None = None,   # e.g. ?status_filter=new
    queue_filter: str | None = None,    # e.g. ?queue_filter=time-off
    db: Session = Depends(get_db),
):
    query = db.query(Ticket)
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    if queue_filter:
        query = query.filter(Ticket.queue == queue_filter)
    return query.order_by(Ticket.needs_review.desc(), Ticket.created_at.desc()).all()


@app.get("/tickets/{ticket_id}", response_model=TicketHR, dependencies=[Depends(require_hr)])
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return get_ticket_or_404(db, ticket_id)


@app.patch("/tickets/{ticket_id}", response_model=TicketHR, dependencies=[Depends(require_hr)])
def update_ticket(ticket_id: int, update: TicketUpdate, db: Session = Depends(get_db)):
    ticket = get_ticket_or_404(db, ticket_id)
    if ticket.status == "approved":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket is already approved")

    if update.reply is not None:              # HR edited the text
        ticket.final_reply = update.reply

    if update.approve:                        # HR approved it
        ticket.final_reply = ticket.final_reply or ticket.draft
        ticket.edited = ticket.final_reply != ticket.draft
        ticket.status = "approved"

        log_event("ticket_approved", ticket_id=ticket.id, edited=ticket.edited)

    db.commit()
    db.refresh(ticket)
    return ticket

@app.get("/stats", response_model=StatsOut, dependencies=[Depends(require_hr)])
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Ticket.id)).scalar()
    in_review = db.query(func.count(Ticket.id)).filter(Ticket.needs_review == True).scalar()
    approved = db.query(func.count(Ticket.id)).filter(Ticket.status == "approved").scalar()
    edited = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.status == "approved", Ticket.edited == True)
        .scalar()
    )
    per_category = db.query(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category).all()

    return StatsOut(
        total_tickets=total,
        approved_tickets=approved,
        review_rate=round(in_review / total, 2) if total else 0.0,
        edited_rate=round(edited / approved, 2) if approved else None,
        tickets_per_category={category or "failed": count for category, count in per_category},
    )