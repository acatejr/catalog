# Use a Python image with uv pre-installed
# FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
FROM python:3.13.4

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip --no-cache-dir


# Install the project into `/app`
WORKDIR /app

# # Then, add the rest of the project source code and install it
# # Installing separately from its dependencies allows optimal layer caching
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
# ENTRYPOINT []

# Run the FastAPI application by default
# Uses `fastapi dev` to enable hot-reloading when the `watch` sync occurs
# Uses `--host 0.0.0.0` to allow access from outside the container
# CMD ["fastapi", "dev", "--host", "0.0.0.0", "src/uv_docker_example"]
CMD ["bash"]