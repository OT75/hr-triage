from fastapi import FastAPI, HTTPException, status
from openai import AuthenticationError, OpenAIError

from app.config import settings
from app.llm import extract
from app.schemas import RequestIn, TicketOut

app = FastAPI(title=settings.app_name)

# Temporary storage until PostgreSQL (Phase 2). Lost on every restart.
tickets: dict[int, dict] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/requests", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_request(request: RequestIn):
    try:
        extraction = extract(request.text)
    except AuthenticationError: # Wrong API Key, The message is vague on purpose: the user doesn’t need to know about our API key.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
    except OpenAIError: # Any other OpenAI failure (network, timeout, outage)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The AI service is unavailable. Please try again in a minute.")

    ticket_id = len(tickets) + 1
    ticket = TicketOut(id=ticket_id, extraction=extraction, needs_review=extraction is None)
    tickets[ticket_id] = {"request": request, "ticket": ticket}
    return ticket