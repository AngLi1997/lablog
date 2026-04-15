#!/bin/sh
set -e

export FLASK_APP="${FLASK_APP:-wsgi.py}"
export FLASK_CONFIG="${FLASK_CONFIG:-production}"

mkdir -p /data /app/logs /app/uploads

flask initdb
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers "${GUNICORN_WORKERS:-2}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-30}" \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    wsgi:app
