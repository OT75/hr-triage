from fastapi import Depends, FastAPI, HTTPException, status
from openai import AuthenticationError, OpenAIError
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (imported so SQLAlchemy registers the Ticket table)
from app.db import Base, engine, get_db

from app.config import settings
from app.llm import draft_reply, extract
from app.models import Ticket
from app.schemas import RequestIn, TicketOut
from app.routing import route

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/requests", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
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

    return TicketOut(
        id=ticket.id,
        extraction=extraction,
        routing=decision,
        draft=draft.reply,                             # the text only
    )