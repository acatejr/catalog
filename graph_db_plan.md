# Graph Database Plan for USFS Catalog Data

## Node Types

**Dataset** — the primary entity
- Properties: `id`, `title`, `abstract`, `purpose`, `description`, `src`

**Keyword** — shared across datasets, ideal for graph traversal
- Properties: `value` (the keyword string)

**Source** (`fsgeodata`, `gdd`, `rda`) — the origin system
- Properties: `name`

**LineageStep** — provenance chain for a dataset
- Properties: `description`, `date`

**Theme** — appears on some records (e.g. `"geospatial"`)
- Properties: `value`

---

## Relationship Types

```
(Dataset)-[:HAS_KEYWORD]->(Keyword)
(Dataset)-[:FROM_SOURCE]->(Source)
(Dataset)-[:HAS_LINEAGE]->(LineageStep)
(LineageStep)-[:NEXT]->(LineageStep)   # ordered chain
(Dataset)-[:HAS_THEME]->(Theme)
```

---

## Why a Graph Fits Well Here

**Keywords are the connective tissue.** Many datasets share keywords like `streamflow`, `hydrology`, `NHD`, `climate change`. In a graph you can query: *"find all datasets related to this one via shared keywords"* — this is expensive in SQL but trivial as a graph traversal.

**Cross-source discovery.** A `(Source)` node with edges to all its datasets lets you quickly answer: *"what does `rda` have that `fsgeodata` doesn't, for the same topic?"*

**Lineage is naturally a chain.** The `lineage` array has an ordered sequence of processing steps. Modeling each as a `LineageStep` node with `NEXT` edges preserves that order and makes it queryable — *"which datasets have more than 3 lineage steps?"* or *"which datasets share the same processing methodology?"*

**Deduplication of keywords.** Right now `"streamflow"` and `"stream flow"` both appear as separate keyword strings across datasets. In a graph, these could be merged into a single `Keyword` node with a canonical form, connecting datasets that are currently siloed.

---

## Example Cypher (Neo4j)

```cypher
// Find datasets sharing keywords with a given dataset
MATCH (d:Dataset {id: "3bb5a4ac..."})-[:HAS_KEYWORD]->(k:Keyword)<-[:HAS_KEYWORD]-(related:Dataset)
WHERE related.id <> d.id
RETURN related.title, count(k) AS shared_keywords
ORDER BY shared_keywords DESC
```

```cypher
// Find all datasets from rda about hydrology
MATCH (d:Dataset)-[:FROM_SOURCE]->(:Source {name: "rda"}),
      (d)-[:HAS_KEYWORD]->(:Keyword {value: "hydrology"})
RETURN d.title
```
