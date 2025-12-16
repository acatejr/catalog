# Claude Code Prompt: MkDocs Documentation

Use this prompt with Claude Code to help write MkDocs documentation for the Catalog project.

## The Prompt

```
I need help writing MkDocs documentation for my "Catalog" project - a Python CLI tool that harvests and catalogs USFS geospatial data from three sources: FSGeodata Clearinghouse, Research Data Archive (RDA), and Geospatial Data Discovery (GDD).

**Project context:**
- Uses ChromaDB for vector storage
- CLI tool built with Click (command: `timbercat`)
- Downloads XML metadata and MapServer JSON service definitions
- Goal: Enable semantic search/querying of USFS datasets

**Documentation needs:**
I want to create a series of MkDocs pages documenting both the technical implementation AND the journey/findings. The docs should be:
- Professional but approachable (suitable for LinkedIn sharing)
- Include lessons learned and insights
- Show both the "how" and the "why"

**Suggested structure:**
1. docs/index.md - Project overview and motivation
2. docs/data-sources.md - Deep dive into the three USFS data sources
3. docs/architecture.md - Technical architecture and design decisions
4. docs/harvesting.md - Data harvesting process and challenges
5. docs/vector-db.md - ChromaDB implementation and semantic search
6. docs/cli.md - CLI usage and examples
7. docs/findings.md - Key insights and discoveries
8. docs/blog/ - Short-form posts for LinkedIn (lessons learned, tips, etc.)

**For each doc page, please:**
1. Read existing relevant source files to understand the implementation
2. Write clear, well-structured Markdown
3. Include code snippets where helpful
4. Add diagrams using Mermaid where appropriate
5. Keep a professional but engaging tone

**Start by:** Reviewing the existing docs/ folder and mkdocs.yml, then propose updates to mkdocs.yml to accommodate the new structure. Ask me which page to start with.
```

## Tips for Using This Prompt

- **Work in stages:** Run it one doc page at a time to maintain quality
- **Create a blog folder:** Ask Claude Code to create `docs/blog/` for LinkedIn-sized posts
- **Preview as you go:** Use `mkdocs serve` to preview documentation changes
- **Enhance visuals:** Consider adding `mkdocs-material` theme extensions for better visuals
- **Iterate:** Ask for revisions or different angles if the first draft doesn't hit the mark

## LinkedIn Post Ideas

Once documentation is complete, consider extracting these topics for LinkedIn posts:

1. "How I Built a CLI Tool to Catalog 400+ USFS Geospatial Datasets"
2. "Using ChromaDB for Semantic Search Over Government Metadata"
3. "Lessons Learned Scraping Federal Agency Data Portals"
4. "Making Public Data More Accessible with Vector Databases"
5. "From XML to Insights: Processing USFS Metadata at Scale"
