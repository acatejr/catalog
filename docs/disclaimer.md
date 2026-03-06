# Disclaimer

## Project Status

Catalog is an independent proof-of-concept research project. It is **not** an official USDA Forest Service product, system, or endorsed tool. It does not represent the position, policy, or direction of the USDA, the Forest Service, or any other federal agency.

## Data Sources

All metadata harvested by this tool is drawn exclusively from **publicly accessible federal open data sources**:

- [FSGeodata Clearinghouse](https://data.fs.usda.gov) — publicly available geospatial metadata
- [Geospatial Data Discovery Hub](https://usfs.maps.arcgis.com) — DCAT-US 1.1 open data feed
- [Research Data Archive](https://www.fs.usda.gov/rds/archive) — publicly published research dataset metadata

No internal, sensitive, restricted, or non-public USFS data is accessed, stored, or processed by this tool. All source data is already available to the public via the above portals.

## AI and Compute Resources

This project was initiated during a period when USDA/USFS policy restricted employee use of AI tools. The approach was designed specifically to work within that constraint:

- AI/LLM inference runs **locally** (via [Ollama](https://ollama.com)) or on [CyVerse](https://cyverse.org), an NSF-funded public research cyberinfrastructure platform operated by the University of Arizona and available to the broader research community.
- No federal data is transmitted to commercial AI APIs.
- All project code resides on a personal workstation or a CyVerse virtual machine—not on USFS-managed systems.

USDA/USFS AI use policies have since evolved. This project's approach—public data only, on-premises or academic compute, no commercial API data transfer—remains consistent with prudent data handling regardless of current policy.

## Intellectual Property and Liability

- This software is provided as-is, without warranty of any kind.
- The project author(s) make no claims regarding the completeness, accuracy, or fitness for purpose of the harvested metadata. Metadata accuracy is the responsibility of the originating data portals.
- Use of this tool for operational or decision-making purposes should be validated against authoritative sources.

## Open Source and Transparency

All source code is publicly available. The methods, data sources, and AI integrations are documented so that the approach can be independently reviewed, reproduced, or adapted.
