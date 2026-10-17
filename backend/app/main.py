from fastapi import Depends, FastAPI, HTTPException, status
from openai import AuthenticationError, OpenAIError
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (imported so SQLAlchemy registers the Ticket table)
from app.db import Base, engine, get_db

from app.auth import require_hr
from app.config import settings
from app.llm import draft_reply, extract
from app.models import Ticket
from app.schemas import RequestIn, TicketCreated, TicketHR, TicketUpdate
from app.routing import route

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- Employee side ----------

@app.post("/requests", response_model=TicketCreated, status_code=status.HTTP_201_CREATED)
def create_request(request: RequestIn, db: Session = Depends(get_db)):  # db: one session per request, closed afterwards
    try:
        extraction = extract(request.text) # 1. LLM: what is it about?
        draft = draft_reply(request.name, request.text, extraction)# 2. LLM: write a reply
    except AuthenticationError: # Wrong API Key, The message is vague on purpose: the user doesn’t need to know about our API key.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
    except OpenAIError: # Any other OpenAI failure (network, timeout, outage)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The AI service is unavailable. Please try again in a minute.")

    decision = route(extraction, draft.fully_answered) # 3. Code: where, and review?

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
    ticket_status: str | None = None,   # e.g. ?ticket_status=new
    queue: str | None = None,           # e.g. ?queue=time-off
    db: Session = Depends(get_db),
):
    query = db.query(Ticket)
    if ticket_status:
        query = query.filter(Ticket.status == ticket_status)
    if queue:
        query = query.filter(Ticket.queue == queue)
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

    db.commit()
    db.refresh(ticket)
    return ticket