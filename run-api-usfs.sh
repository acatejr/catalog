#!/bin/bash
PYTHONPATH=/home/ubuntu/workspace/github.com/acatejr/catalog/src uvicorn catalog.api.api:api "$@"
