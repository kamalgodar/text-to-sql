FROM python:3.12-slim-bookworm

# Install uv package installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt .
COPY app.py .
COPY src/ ./src/

RUN uv venv
RUN uv pip install -r requirements.txt

EXPOSE 9000

CMD ["/app/.venv/bin/uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "9000"]