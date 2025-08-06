# Python Docker Container

This repository contains a Dockerfile for running the latest version of Python using the most efficient Docker image (`python:alpine`).

## Features

- **Efficient Base Image**: Uses `python:alpine` which is significantly smaller than standard Python images
- **Latest Python**: Automatically uses the latest Python version available
- **Fast Package Management**: Includes `uv` for extremely fast Python package installation
- **Security**: Runs as non-root user for enhanced security
- **Optimized**: Includes environment variables for optimal Python performance
- **Ready to Use**: Includes a demo application to verify functionality

## Quick Start

### Build the Docker Image

```bash
docker build -t python-app .
```

### Run the Container

```bash
docker run --rm python-app
```

### Run Interactively

```bash
docker run --rm -it python-app /bin/sh
```

### Run with Volume Mount (for development)

```bash
docker run --rm -v $(pwd):/app python-app
```

## Image Details

- **Base Image**: `python:alpine`
- **Size**: Approximately 50MB (vs 900MB+ for standard Python images)
- **Python Version**: Latest available
- **Security**: Non-root user execution
- **Performance**: Optimized environment variables

## Customization

### Adding Dependencies with uv (Recommended)

`uv` is included for extremely fast package installation. You have two options:

#### Option 1: Using requirements.txt with uv
1. Create a `requirements.txt` file with your Python dependencies
2. Uncomment the relevant lines in the Dockerfile:
   ```dockerfile
   COPY requirements.txt .
   RUN uv pip install --system -r requirements.txt
   ```

#### Option 2: Using pyproject.toml with uv (Modern approach)
1. Create a `pyproject.toml` file with your project configuration
2. Uncomment the relevant lines in the Dockerfile:
   ```dockerfile
   COPY pyproject.toml uv.lock* ./
   RUN uv sync --frozen
   ```

### Adding Dependencies with pip (Traditional)

If you prefer using pip instead of uv:
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

### System Dependencies

If you need system packages, uncomment and modify:
```dockerfile
RUN apk add --no-cache gcc musl-dev
```

### Port Configuration

Modify the `EXPOSE` directive if your application uses a different port:
```dockerfile
EXPOSE 3000
```

## File Structure

```
.
├── Dockerfile          # Docker configuration
├── app.py             # Demo Python application
├── README.md          # This file
├── .dockerignore      # Docker ignore patterns
├── .editorconfig      # Editor configuration
└── .gitignore         # Git ignore patterns
```

## Why Alpine?

Alpine Linux is chosen for its:
- **Small size**: ~5MB base image
- **Security**: Minimal attack surface
- **Performance**: Fast startup times
- **Compatibility**: Full Python functionality
