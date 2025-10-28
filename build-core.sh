#!/bin/bash

# Build the Core Docker image
docker build -f Dockerfile.core -t catalog-core .
