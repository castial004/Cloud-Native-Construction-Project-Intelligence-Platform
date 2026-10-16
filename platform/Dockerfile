# Shared image for all CCPIP Python services (paper Sec. VI: python:3.10-slim).
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for psycopg2 build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY common ./common
COPY db ./db
COPY services ./services
COPY datagen ./datagen
COPY powerbi ./powerbi
COPY eval ./eval

RUN pip install .

# Default command is overridden per-service in compose / k8s.
CMD ["python", "-c", "print('specify a service command')"]
