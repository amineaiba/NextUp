# Virtual Queue

A virtual queue app — join a line from your phone, see your spot, get notified when it's your turn. No more standing in a room for hours.

Work in progress.

## Stack

FastAPI · async SQLAlchemy · PostgreSQL · Alembic

## Run

```bash
docker compose up -d db
cd backend
pip install -r requirements.txt
alembic upgrade head
psql postgresql://user:password@localhost:5433/virtualqueue -f seeds/dev_seed.sql  # optional dev data
uvicorn app.main:app --reload
```

Docs at `http://localhost:8000/docs`.

## Endpoints

| Method | Path | What |
|---|---|---|
| POST | `/queues/{queue_id}/join` | client joins, gets a position |
| POST | `/queues/{queue_id}/call-next` | staff calls next person to a counter |
| POST | `/entries/{entry_id}/done` | staff marks the person served |
| GET | `/health` | liveness check |
