# Prompts

### Simple

The simple prompt turns the assistant into a straightforward catalog Q&A helper. It answers user questions using only the search results returned from the catalog, sorts those results by how closely they match the query, and refuses to speculate or invent information that isn't there. If a question can't be answered from the catalog, it says so plainly. This is the default prompt and works well for quick, direct lookups.

### Discovery

The discovery prompt frames the assistant as a knowledgeable USFS data librarian whose job is to help users find the right datasets. For each result it explains what the dataset contains, which source system it comes from, and why it's a good match for the query. If the user asks whether data exists on a topic, the assistant answers yes or no first, then lists what it found. When nothing relevant turns up, it suggests alternative search terms rather than leaving the user stuck. A set of persona variants — analyst, forester, manager, general public, and elected official — are also available, each tailoring the depth and language of the response to that audience.

### Relationships

The relationships prompt guides the assistant to look across datasets and surface connections that may never have been formally documented. It identifies datasets that cover the same subject matter or geography, flags potential duplicates spread across the three source systems, highlights datasets that would be more useful when combined, and notes cases where a logical connection between datasets is missing entirely. The assistant distinguishes between relationships that are explicitly stated in the metadata and those it is inferring from thematic or geographic similarity, so users know how much confidence to place in each finding.

### Lineage

The lineage prompt focuses on where a dataset came from and whether it can be trusted. The assistant walks through a dataset's origin — who created it, when, and for what purpose — then traces its processing history in chronological order, covering how the data was collected, what changes were made over time, and whether it was derived from another dataset. If the provenance information is incomplete or missing, the assistant says so clearly rather than guessing. Like the discovery prompt, lineage also supports persona variants so the same underlying history can be explained in the right terms for a GIS analyst, a field forester, a manager, a member of the public, or a policy official.
