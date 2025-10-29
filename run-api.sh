#!/bin/bash
PYTHONPATH=src uvicorn catalog.api.api:api "$@"
