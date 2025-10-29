#!/bin/bash
PYTHONPATH=/home/ubuntu/workspace/github.com/acatejr/catalog/src /home/ubuntu/workspace/github.com/acatejr/catalog/.venv/bin/uvicorn catalog.api.api:api "$@"
