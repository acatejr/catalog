#!/bin/bash

# Build the core image first (required as base)
docker build -f Dockerfile.core -t catalog-core .

# Build the CLI Docker image
docker build -f Dockerfile.cli -t catalog-cli .
