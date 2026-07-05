from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from domain.entities.models import SupportTicket
from domain.ports.support_agent import new_request_id
from fastapi import FastAPI, HTTPException

from api.dependencies import get_investigate_use_case, get_ingest_use_case, get_request_logger
from infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-ingest documents if vector store is empty."""
    try:
        ingest = get_ingest_use_case()
        count = await ingest.execute(force=False)
        app.state.ingested_chunks = count
    except Exception as exc:
        app.state.ingested_chunks = 0
        app.state.ingest_error = str(exc)
    yield


app = FastAPI(
    title="NovaTech Intelligent Support Agent",
    description="Autonomous support ticket investigation agent",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "ingestedChunks": getattr(app.state, "ingested_chunks", 0),
    }


@app.post("/api/v1/investigate")
async def investigate(ticket: SupportTicket) -> dict[str, object]:
    request_id = new_request_id()
    settings = get_settings()
    model_name = {
        "groq": settings.groq_model,
        "nvidia": settings.nvidia_model,
        "openai": settings.openai_model,
        "ollama": settings.ollama_model,
    }.get(settings.llm_provider.lower(), "unknown")
    logger.info(
        "POST /api/v1/investigate request_id=%s llm=%s model=%s customer=%s subject=%r",
        request_id,
        settings.llm_provider,
        model_name,
        ticket.customer,
        ticket.subject,
    )
    use_case = get_investigate_use_case()
    try:
        report = await use_case.execute(ticket, request_id)
    except Exception as exc:
        logger.exception("Investigation failed request_id=%s", request_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    logger.info("Investigation completed request_id=%s", request_id)

    request_logger = get_request_logger()
    return {
        "report": report.model_dump(mode="json"),
        "logPath": request_logger.get_log_path(request_id),
    }


@app.post("/api/v1/ingest")
async def ingest_documents(force: bool = False) -> dict[str, object]:
    ingest = get_ingest_use_case()
    try:
        count = await ingest.execute(force=force)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"chunksIngested": count}
