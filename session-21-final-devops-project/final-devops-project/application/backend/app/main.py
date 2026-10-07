import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .models import Ticket
from .schemas import StatsOut, TicketCreate, TicketOut, TicketUpdate

VERSION = "1.0.0"

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("helpdesk")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # In the container Alembic creates the table before uvicorn starts.
    # create_all only matters for the tests (SQLite) and does nothing if the table exists.
    Base.metadata.create_all(bind=engine)
    log.info("starting %s version=%s env=%s db_host=%s", settings.app_name, VERSION, settings.app_env, settings.db_host)
    yield


app = FastAPI(title=settings.app_name, version=VERSION, lifespan=lifespan)

# /metrics for Prometheus (request count, latency, sizes per handler)
Instrumentator(excluded_handlers=["/metrics", "/health", "/ready"]).instrument(app).expose(app, endpoint="/metrics")


def get_ticket_or_404(ticket_id: int, db: Session) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.get("/")
def root():
    return {"service": settings.app_name, "version": VERSION, "env": settings.app_env, "docs": "/docs"}


@app.get("/health")
def health():
    # liveness: the process is alive
    return {"status": "UP"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    # readiness: we can talk to the database
    db.execute(text("SELECT 1"))
    return {"status": "READY"}


@app.get("/api/info")
def info():
    return {"app": settings.app_name, "version": VERSION, "env": settings.app_env}


@app.get("/api/tickets", response_model=list[TicketOut])
def list_tickets(db: Session = Depends(get_db)):
    return list(db.scalars(select(Ticket).order_by(Ticket.id.desc())))


@app.get("/api/tickets/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    rows = db.execute(select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)).all()
    counts = {row[0]: row[1] for row in rows}
    return StatsOut(
        total=sum(counts.values()),
        open=counts.get("OPEN", 0),
        inProgress=counts.get("IN_PROGRESS", 0),
        resolved=counts.get("RESOLVED", 0),
    )


@app.get("/api/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return get_ticket_or_404(ticket_id, db)


@app.post("/api/tickets", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    log.info("ticket created id=%s priority=%s category=%s", ticket.id, ticket.priority, ticket.category)
    return ticket


@app.put("/api/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)):
    ticket = get_ticket_or_404(ticket_id, db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticket, key, value)
    db.commit()
    db.refresh(ticket)
    log.info("ticket updated id=%s status=%s", ticket.id, ticket.status)
    return ticket


@app.delete("/api/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = get_ticket_or_404(ticket_id, db)
    deleted_id = ticket.id  # log the id from the database, not the raw value from the URL (CodeQL py/log-injection)
    db.delete(ticket)
    db.commit()
    log.info("ticket deleted id=%s", deleted_id)
