"""APEX XI serving API."""
import logging
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .db import DbUnavailable, get_db
from . import queries

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="APEX XI API", version="0.3.0",
              description="Read-only serving API over apex.duckdb (historic + live).")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(DbUnavailable)
async def _db_unavailable(request: Request, exc: DbUnavailable):
    return JSONResponse(status_code=503, content={"detail": "data store unavailable"})

@app.get("/health")
def health(con=Depends(get_db)):
    return {"status": "ok", "tables": queries.table_counts(con)}

@app.get("/api/meta")
def meta(con=Depends(get_db)):
    return queries.meta(con)

# Routers (created as stubs in Step 4, fleshed out in Tasks 4 & 5):
from .routers import historic, live   # noqa: E402
app.include_router(historic.router)
app.include_router(live.router)
