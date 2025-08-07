# Use the official Python Alpine image (most efficient)
FROM python:3.13.4

# Expose port (adjust as needed)
EXPOSE 8000

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies if needed (uncomment as required)
RUN apt-get update -y && apt-get upgrade --fix-missing -y && \
    apt-get install -y build-essential curl && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir uv

# RUN apt-get update -y && apt-get upgrade --fix-missing -y
# RUN apt-get install -y build-essential curl && \
#     rm -rf /var/lib/apt/lists/* && \
#     pip install --no-cache-dir uv

# Copy the application code
WORKDIR /app
COPY . .

# Download the latest installer
# ADD https://astral.sh/uv/install.sh /uv-installer.sh
# Run the installer then remove it
# RUN sh /uv-installer.sh && rm /uv-installer.sh
# Ensure the installed binary is on the `PATH`
# ENV PATH="/root/.local/bin/:$PATH"

# Install Python dependencies (if you have requirements.txt)
# RUN pip install --no-cache-dir -r requirements.txt


# RUN uv sync

# RUN useradd -m -s /bin/bash appuser && \
#     chown -R appuser:appuser /app

# USER appuser

# Default command (adjust based on your application)
# CMD ["python", "main.py"]
