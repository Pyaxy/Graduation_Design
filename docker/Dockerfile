# image source: Python 3.11
FROM python:3.11-slim

# SET ENV
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# SET workdir
WORKDIR /code


# Install essential package
RUN apt-get update && apt-get install -y \
  gcc \
  python3-dev \
  libpq-dev \
  build-essential \
  netcat-openbsd \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

