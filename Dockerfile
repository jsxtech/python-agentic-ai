FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py .
COPY .env.example .env

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the agent
CMD ["python", "agent.py"]
