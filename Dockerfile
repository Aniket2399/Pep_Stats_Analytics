# PepStats serving API — self-contained image (ships the pre-built apex.duckdb).
FROM python:3.13-slim

WORKDIR /app

# Install only the serving deps (see requirements-api.txt).
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# App code + the 3.3 MB serving database.
COPY apex/ ./apex/
COPY data/serving/apex.duckdb ./data/serving/apex.duckdb

# Render/Fly/Railway inject $PORT; default to 8000 locally.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn apex.api.app:app --host 0.0.0.0 --port ${PORT}"]
