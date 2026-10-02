# Server image: minimal Flask + Gunicorn
FROM python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates openssh-client \
 && rm -rf /var/lib/apt/lists/*

# Copy project description, to instal dependencies
COPY pyproject.toml /app/pyproject.toml
COPY requirements.lock /app/requirements.lock

# Install runtime dependencies
RUN pip install --no-cache-dir -r requirements.lock

# Copy sources after dependencies installation
COPY src /app/src
COPY keys /app/keys
COPY flag /app/flag
COPY entrypoint.sh /app/entrypoint.sh
RUN pip install --no-cache-dir --no-deps -e .

EXPOSE 5000

# Default command runs the web server
CMD ["./entrypoint.sh"]

