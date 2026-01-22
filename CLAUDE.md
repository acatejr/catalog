# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Catalog is a Python CLI tool for downloading and managing geospatial data from the USFS Geodata Clearinghouse. The project focuses on fetching metadata (XML) and web services information (JSON) from https://data.fs.usda.gov.

### Code Quality

```bash
# Format and lint with ruff (configured as dev dependency)
ruff check .
ruff format .
```

## Instructions

When running, IGNORE data/catalog.json.  I do NOT want to consume tokens or use up my Anthropic token limits.
If you don't know the answer to something, don't guess, just say you don't know.
