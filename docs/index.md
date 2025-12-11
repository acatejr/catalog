# Catalog: A CLI Tool for Downloading USFS Geospatial Data

The U.S. Forest Service (USFS) has a wealth of geospatial and tabluar data. Accessing this data typically involves navigating the websites, browsing through hundreds of datasets, and manually downloading metadata XML files and MapServer service URLs for each dataset you need. For researchers and developers working with multiple datasets, this manual process can become a bottleneck.  Often questions like:  

- Where is a specific data set stored?
- What data sets are recommended for building a dashboard?
- What is the data lineage of a specific dataset?

That's why I built **Catalog** - a Python CLI tool that automates the entire process.

## What Does Catalog Do?

Catalog fetches metadata and web service information from the USFS Geodata Clearinghouse with a single command. It:

- Scrapes the datasets page to find all available datasets
- Downloads XML metadata files for each dataset
- Extracts and saves MapServer service definitions as JSON
- Organizes everything in a clean directory structure

## Quick Start

Installation is straightforward with `uv` (or pip):

```bash
# Install with uv
uv sync

# Or use pip in development mode
pip install -e .
```

Then run it:

```bash
# Download all USFS geodata metadata and services
cod download-fsgeodata
```

That's it. Catalog handles the rest, downloading files to a structured `data/fsgeodata/` directory:

```
data/fsgeodata/
├── metadata/     # XML metadata for each dataset
└── services/     # JSON MapServer service definitions
```

## Why I Built This

I needed a reliable way to access USFS geospatial data programmatically. Manual downloading doesn't scale, and there wasn't an existing tool that did this specific job. I wanted something that:

- **Respects the server**: Built-in rate limiting (0.5s between requests) to avoid overwhelming data.fs.usda.gov
- **Handles errors gracefully**: If one dataset fails, it continues with the rest
- **Provides clear feedback**: Uses Rich console output to show progress
- **Organizes data logically**: Separates metadata from service definitions

## Technical Approach

Catalog is built with Python 3.14+ and uses:

- **Click** for the CLI interface
- **BeautifulSoup** for parsing the datasets page
- **requests** with session management for efficient HTTP operations
- **Rich** for beautiful terminal output
- **pathlib** for cross-platform file handling

The core is the `FSGeodataDownloader` class, which handles scraping, downloading, and organizing files. It uses a `requests.Session` with custom headers and implements rate limiting to be a good citizen of the USFS servers.

## What's Next

This is just the beginning. I'm currently working on:

- ChromaDB integration for vector search across metadata
- API endpoints for programmatic access
- Additional data sources beyond USFS
- Better filtering and search capabilities

The project is open source and available on GitHub. If you work with geospatial data or have ideas for improving the tool, I'd love to hear from you.

## Try It Out

Check out the [repository](https://github.com/acatejr/catalog) and give it a try. If you find it useful or have suggestions, open an issue or submit a PR. I'm excited to see where this project goes.

---

*Have you built tools for working with geospatial data? What challenges have you encountered? Drop a comment below.*
