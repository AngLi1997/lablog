FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    FLASK_APP=wsgi.py \
    FLASK_CONFIG=production \
    PATH="/app/.venv/bin:/root/.local/bin:${PATH}"

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir uv \
    && uv venv /app/.venv \
    && uv pip install --python /app/.venv/bin/python -r /app/requirements.txt

COPY . /app

RUN mkdir -p /data /app/logs /app/uploads

EXPOSE 5000

CMD ["sh", "/app/docker/start.sh"]
