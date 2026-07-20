import logging

from fastapi import FastAPI

from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Virtual Queue")


@app.get("/health")
async def health():
    logger.info("health check hit")
    return {"status": "ok"}
