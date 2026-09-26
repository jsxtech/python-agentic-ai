FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

ENV PYTHONUNBUFFERED=1

# Run as a non-root user (defense in depth for file/code-execution tools).
# Create the runtime directories the agents write to and hand ownership to the
# unprivileged user before dropping privileges.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/workspace /app/knowledge /app/logs \
    && chown -R appuser:appuser /app
USER appuser

CMD ["python", "agent.py"]
