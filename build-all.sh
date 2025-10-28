#!/bin/bash

echo "Building catalog-core..."
docker build -f Dockerfile.core -t catalog-core .

echo "Building catalog-cli..."
docker build -f Dockerfile.cli -t catalog-cli .

echo "Building catalog-api..."
docker build -f Dockerfile.api -t catalog-api .

echo "All images built successfully!"
