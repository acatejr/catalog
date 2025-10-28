# Architecture Recommendations for Catalog Project

## Current Architecture Assessment

Your project has three main components:

- **CLI**: Data ingestion pipeline (download, parse, embed, store)
- **API**: Query interface (FastAPI with RAG)
- **Shared layer**: Database operations, schemas, LLM integration

**Key insight**: The CLI and API are operationally independent but share critical infrastructure (database schema, vector operations).

## Architectural Options

### Option 1: Monorepo with Better Structure (Recommended)

Keep everything in one repo but reorganize:

```
catalog/
├── packages/
│   ├── catalog-core/          # Shared library
│   │   ├── __init__.py
│   │   ├── db.py
│   │   ├── schema.py
│   │   └── config.py
│   ├── catalog-cli/           # CLI tools
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── downloaders/
│   │   └── parsers/
│   └── catalog-api/           # Web API
│       ├── __init__.py
│       ├── api.py
│       ├── llm.py
│       └── routes/
├── docker/
│   ├── Dockerfile.cli
│   ├── Dockerfile.api
│   └── docker-compose.yml
├── tests/
│   ├── core/
│   ├── cli/
│   └── api/
└── docs/
```

**Pros:**

- Atomic commits across components
- Shared code is trivial to update
- Single CI/CD pipeline
- Easy local development
- Can still deploy API and CLI separately via Docker

**Cons:**

- Slightly larger repo
- Need discipline to maintain boundaries

**When to choose**: This is ideal for small-to-medium projects with 1-3 developers, especially POCs.

### Option 2: Separate Repos with Shared Package

Split into three repos:

1. **`catalog-core`** (shared library)
   - db.py, schema.py, config
   - Published as pip package

2. **`catalog-cli`** (CLI tools)
   - Depends on catalog-core
   - Data ingestion logic

3. **`catalog-api`** (web API)
   - Depends on catalog-core
   - FastAPI endpoints and LLM

**Pros:**

- True separation of concerns
- Independent versioning and deployment
- Teams can own different repos
- Clear API boundaries

**Cons:**

- Coordinating changes to shared code is harder
- Need to publish and version catalog-core
- More complex setup (3 repos, package management)
- Breaking changes in core affect both CLI and API

**When to choose**: When you have multiple teams, need independent release cycles, or the project is production-grade with many developers.

### Option 3: Microservices Architecture

Convert CLI to a background worker service:

```
catalog-api/          # FastAPI application
catalog-worker/       # Background job processor (former CLI)
catalog-core/         # Shared library
```

- CLI commands become API endpoints or async jobs
- Worker processes ingestion tasks from queue (RabbitMQ, Redis)
- API can trigger ingestion programmatically

**Pros:**

- Scalable architecture
- API can trigger data refreshes
- Modern microservices pattern

**Cons:**

- Significant complexity increase
- Need message queue infrastructure
- Overkill for POC

**When to choose**: Production system with high scale or need programmatic data refresh.

### Option 4: Hybrid Monorepo

Keep current structure but clarify boundaries:

```
catalog/
├── src/
│   ├── core/          # Shared (db, schema)
│   ├── cli/           # CLI only
│   └── api/           # API only
├── Dockerfile.cli     # Separate images
├── Dockerfile.api
└── docker-compose.yml # Both services
```

**Pros:**

- Minimal refactoring
- Clear separation
- Keeps simplicity
- Can still deploy separately

**Cons:**

- Less structured than Option 1

## Recommendation

**For your POC stage: Option 4 (Hybrid Monorepo) → Option 1 (Structured Monorepo)**

### Why This Approach?

1. **You're still in POC phase**: The project is described as "proof-of-concept." Premature splitting adds unnecessary complexity.

2. **High coupling on database schema**: CLI and API both depend heavily on the vector database schema. Any schema change requires coordinated updates.

3. **Deployment independence already possible**: With Docker, you can deploy CLI and API as separate containers from one repo.

4. **Simple coordination**: For a single developer or small team, monorepo keeps things simple while maintaining clear boundaries.

## Immediate Action Plan

### Step 1: Reorganize Current Structure (Option 4)

```bash
src/
├── core/
│   ├── __init__.py
│   ├── db.py
│   └── schema.py
├── cli/
│   ├── __init__.py
│   └── cli.py
└── api/
    ├── __init__.py
    ├── api.py
    └── llm.py
```

### Step 2: Create Separate Dockerfiles

- `Dockerfile.cli` - For data ingestion tasks
- `Dockerfile.api` - For web service

### Step 3: Update Compose File

Configure docker-compose.yml to run both services with appropriate dependencies.

### Step 4: Add Clear Documentation

Document which services do what and how they interact.

## When to Split Repos

Consider splitting into separate repositories when:

- You have 3+ developers working on different components
- You need truly independent release cycles
- CLI and API have different security/compliance requirements
- You're transitioning from POC to production with separate teams
- The shared core is stable and changes infrequently

## Migration Path

As your project matures:

1. **Phase 1 (Now)**: Implement Option 4 - Hybrid Monorepo
2. **Phase 2 (Growth)**: Move to Option 1 - Structured Monorepo with packages
3. **Phase 3 (Scale)**: Consider Option 2 - Separate repos if team grows significantly
4. **Phase 4 (Production)**: Evaluate Option 3 - Microservices if scale demands it

## Additional Considerations

### Current Shared Dependencies

| Module | CLI Usage | API Usage | Purpose |
|--------|-----------|-----------|---------|
| `schema.py` | Document validation during parsing | Request/response types | Data models |
| `db.py` | Data ingestion & storage | Search & retrieval | Database operations |
| `llm.py` | ❌ Not used | Query responses | LLM integration |

### Architecture Diagram

```
CLI (cli.py)                         API (api.py)
├─ Downloads                         ├─ /health
├─ Parsing                           ├─ /query
├─ Embedding                         └─ Uses ChatBot
└─ Storage                                  ↓
    ↓                               LLM Integration (llm.py)
    └────────────────────────────────────────────┘
              Shared Components
              ├─ db.py (Vector DB ops)
              ├─ schema.py (Data models)
              └─ PostgreSQL with pgvector
```

## Conclusion

Start with Option 4 (Hybrid Monorepo) for immediate improvement with minimal effort. This maintains simplicity while establishing clear boundaries. As the project grows and requirements change, you can naturally evolve toward more structured options.

The key is to maintain flexibility and avoid premature optimization while keeping code organized and maintainable.
