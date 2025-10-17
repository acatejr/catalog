FROM python:3.14-slim

# Install system dependencies for PostGIS and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    binutils \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
# RUN pip install --upgrade pip && pip install uv
RUN pip install --upgrade pip

# Set working directory
WORKDIR /app
COPY . /app/
RUN pip install -r requirements.txt

