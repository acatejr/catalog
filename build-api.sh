#!/bin/bash

# Build the core image first (required as base)
docker build -f Dockerfile.core -t catalog-core .

# Build the API Docker image
docker build -f Dockerfile.api -t catalog-api .
