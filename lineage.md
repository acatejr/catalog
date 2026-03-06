# Lineage in Metadata

In metadata, **lineage** describes the history and provenance of a dataset — essentially answering: *"Where did this data come from and how was it processed?"*

It typically includes:

- **Source** — the original data source(s) used to create the dataset
- **Processing steps** — transformations, conversions, or edits applied to the data
- **Dates** — when data was collected, processed, or published
- **Methods** — tools, algorithms, or procedures used
- **Responsible parties** — who collected or processed it

In geospatial metadata (like FGDC or ISO 19115 standards used by USFS), lineage is a key section that helps users assess **data quality and trustworthiness** — if you know how data was collected and processed, you can better judge whether it's fit for your purpose.

## Example Questions About Lineage in General

1. "What is data lineage and why does it matter?"
2. "How do I document the lineage of a dataset?"
3. "What information should be included in the lineage section of metadata?"
4. "How does lineage help me evaluate whether a dataset is trustworthy?"
5. "What is the difference between data lineage and data provenance?"

## Example Questions About a Specific Dataset's Lineage

1. "Where did this dataset originally come from?"
2. "What processing steps were applied to this data before it was published?"
3. "Who collected this data and when was it gathered?"
4. "Has this dataset been reprojected or transformed from its original format?"
5. "What source data or imagery was used to create this dataset?"

## Plan: Adding Lineage Query Functionality

### Current State

The app already stores lineage data in `USFSDocument.lineage` (a list of dicts with `description` and `date` fields) and embeds it into ChromaDB via `extract_lineage_info()` in `core.py`. However, there are gaps that prevent answering specific lineage questions well:

1. **Lineage is dropped on retrieval** — `core.py:query()` hardcodes `lineage=None` when reconstructing documents from ChromaDB results, so lineage data never reaches the user.
2. **Lineage stored as a flat string** — ChromaDB metadata flattens lineage to a single string, losing the structured `description`/`date` fields.
3. **No lineage-focused LLM prompt** — the system prompt in `bots.py` guides the LLM toward dataset *discovery*, not lineage explanation.
4. **No dedicated CLI command** — there is no `query_lineage` command; users have no direct way to ask lineage questions.
5. **No lineage tool for the agent** — `AgentBot` in `bots.py` has no tool it can call to fetch structured lineage for a specific dataset.

---

### Step 1 — Fix Lineage Preservation in `core.py`

**File:** `src/catalog/core.py`

- In `batch_load_documents()`, store lineage as a JSON string in ChromaDB metadata instead of the current flat formatted string. This preserves structure for retrieval.
- In `query()`, parse the stored JSON string back into a list of dicts and populate `doc.lineage` instead of setting it to `None`.

**Answers enabled:** All five questions become possible once lineage data flows through to query results.

---

### Step 2 — Add a Lineage-Focused LLM System Prompt

**File:** `src/catalog/bots.py`

- Add a new `LINEAGE_MESSAGE_CONTENT` system prompt string that instructs the LLM to act as a data provenance expert, specifically covering:
  - Original data source and collection method
  - Chronological processing steps with dates
  - Responsible parties and agencies
  - Transformations (reprojection, format changes, edits)
  - Source datasets or imagery used as inputs
- Add a `lineage_chat(question, context)` method to `OllamaBot` that uses this prompt.

---

### Step 3 — Add `query_lineage` CLI Command

**File:** `src/catalog/cli.py`

- Add a new `query_lineage` command that accepts `--qstn` and `--nresults` options.
- The command searches ChromaDB for the most relevant dataset, then formats its full lineage (structured steps with dates) and passes it to `OllamaBot.lineage_chat()`.
- Output is rendered in a styled Rich panel, similar to `ollama_chat`.

Example usage:

```bash
catalog query_lineage -q "Where did the roads dataset come from?"
catalog query_lineage -q "What processing steps were applied to the trail data?"
```

---

### Step 4 — Add `get_lineage` Tool for `AgentBot`

**File:** `src/catalog/tools.py`

- Add a `get_lineage` tool definition to the `TOOLS` list with a description explaining it retrieves full provenance/lineage for a named dataset.
- Implement the tool handler in `execute_tool()` to look up a dataset by title keyword and return its structured lineage as formatted text.
- This allows `AgentBot` to autonomously answer lineage questions during agentic search sessions via `agent_search`.

---

### Step 5 — Improve Lineage Display in `schema.py`

**File:** `src/catalog/schema.py`

- Update `to_markdown()` (or `USFSDocument`) to render lineage as a numbered list of steps when lineage data is present, showing date and description for each entry.
- This improves output for both `query_fs_chromadb` and the new `query_lineage` command.

---

### Summary of Changes

|File|Change|
|---|---|
|`core.py`|Store lineage as JSON string; restore it on query|
|`bots.py`|Add lineage system prompt + `lineage_chat()` method|
|`cli.py`|Add `query_lineage` CLI command|
|`tools.py`|Add `get_lineage` tool for `AgentBot`|
|`schema.py`|Render lineage as structured list in `to_markdown()`|

---

## Can pgai Improve the Lineage Plan?

Yes. pgai would meaningfully improve several parts of the plan.

### Where pgai Helps Specifically

#### Step 1 — Lineage Preservation

The current ChromaDB approach is forced to flatten lineage into a string because ChromaDB metadata values must be scalars. With pgai, lineage can be stored as a native PostgreSQL `JSONB` column, preserving full structure (all `description`/`date` entries) without any serialization hack.

```sql
ALTER TABLE documents ADD COLUMN lineage JSONB;
```

No more JSON string encoding/decoding in `core.py`.

---

#### Step 3 — Lineage Queries

With pgai + PostgreSQL, you can go beyond semantic similarity and write precise SQL to filter or retrieve lineage:

```sql
-- Find datasets processed after a specific date
SELECT title, lineage
FROM documents
WHERE lineage @> '[{"date": "2020"}]'
ORDER BY distance ASC;
```

This answers questions like *"Has this dataset been transformed?"* or *"Who processed it?"* with far more precision than embedding similarity alone.

---

**Step 4 — `get_lineage` Tool for AgentBot**

Instead of the agent fuzzy-searching for a dataset and hoping lineage comes back, it could call a SQL-backed tool that does an exact or structured lookup — much more reliable for provenance questions.

---

### What Doesn't Change

Steps 2 and 5 (`bots.py` prompt and `schema.py` rendering) are unaffected by pgai — those improvements are needed regardless.

---

### Summary

|Plan Step|With ChromaDB|With pgai|
|---|---|---|
|Lineage storage|JSON string (lossy)|Native `JSONB` (lossless)|
|Lineage retrieval|Parse string back to dict|Direct structured query|
|Date/source filtering|Not possible|Full SQL on JSONB fields|
|Agent tool precision|Fuzzy vector lookup|Exact or filtered SQL query|

pgai doesn't change *what* needs to be built, but it makes Steps 1, 3, and 4 significantly cleaner and more powerful.
