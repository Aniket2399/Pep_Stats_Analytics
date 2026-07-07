"""Read-only DuckDB access for the serving API."""
import duckdb
from apex import config

class DbUnavailable(Exception):
    """Raised when the serving DB is missing or write-locked."""

def get_connection():
    path = config.DUCKDB_PATH
    if not path.exists():
        raise DbUnavailable(f"serving db not found at {path}")
    try:
        return duckdb.connect(str(path), read_only=True)
    except duckdb.Error as e:      # e.g. another process holds the write lock
        raise DbUnavailable(str(e))

def table_exists(con, name: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = ? AND table_schema = 'main'", [name]
    ).fetchone()
    return row is not None

def get_db():
    """FastAPI dependency: yield a read-only connection, always close it.

    Lives here (not in app.py) so routers import it without a circular dependency.
    A raised DbUnavailable is turned into a 503 by app.py's exception handler.
    """
    con = get_connection()
    try:
        yield con
    finally:
        con.close()
