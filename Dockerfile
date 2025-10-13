FROM python:3.13-slim AS base

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv===0.6.4

RUN uv sync --no-cache --frozen

COPY app ./app
COPY README.md ./

RUN useradd -m botuser
RUN mkdir -p /app/app && chown -R botuser:botuser /app
USER botuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_NO_CACHE=1

CMD ["uv", "run", "python", "-m", "app.main"]
