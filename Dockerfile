FROM python:3.13.4

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip --no-cache-dir \
    && pip install uv --no-cache-dir

ENV UV_NO_CACHE=true

# Install the project into `/app`
WORKDIR /app
# ADD pyproject.toml .
# ADD uv.lock .

# RUN uv sync --locked
