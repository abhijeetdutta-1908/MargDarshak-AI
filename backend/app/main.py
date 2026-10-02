import logging

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.routers import auth, catalog, users

log = logging.getLogger("margdarshak")

app = FastAPI(
    title="Margdarshak API",
    description="AI-Based Smart Trip & Travel Planner",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(catalog.router)


@app.exception_handler(SQLAlchemyError)
def db_error(request: Request, exc: SQLAlchemyError):
    log.exception("Database error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=503, content={"detail": "The database is temporarily unavailable. Please retry."})


@app.get("/api/health", tags=["system"], summary="Service and database health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        log.exception("Database health check failed")
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "unreachable", "version": app.version},
        )
    return {"status": "ok", "database": "ok", "version": app.version}
