# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# System deps for Postgres client
RUN apt-get update && apt-get install -y gcc libpq-dev netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static during build
RUN python manage.py collectstatic --noinput

# Stage 2: Production
FROM python:3.12-slim

WORKDIR /app

# Copy code from builder
COPY --from=builder /app /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install netcat
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copy wait-for-db script
COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

# Non-root user
RUN adduser --disabled-password django

# Make /app writable by django user
RUN chown -R django:django /app

# Switch to non-root user
USER django

ENTRYPOINT ["/wait-for-db.sh"]
CMD ["gunicorn", "paygate_project.wsgi:application", "--bind", "0.0.0.0:8000"]
