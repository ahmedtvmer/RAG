FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN UV_HTTP_TIMEOUT=600 uv sync --frozen --no-dev

COPY . .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["curl", "-f", "http://localhost:8080/health"] || exit 1

CMD ["uv", "run", "uvicorn", "api:api", "--host", "0.0.0.0", "--port", "8080"]