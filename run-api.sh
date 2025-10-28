#!/bin/bash
# PYTHONPATH=src uvicorn catalog.api.api:api --reload
PYTHONPATH=src uvicorn catalog.api.api:api "$@"

#!/bin/bash
# PYTHONPATH=src .venv/bin/python -m catalog.cli.cli "$@"