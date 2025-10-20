-- Migration: Add unique constraint for upsert functionality
-- This allows ON CONFLICT to work in bulk_upsert_to_vector_db()

-- Add unique constraint on (doc_id, chunk_index)
-- This will fail if there are existing duplicate rows
ALTER TABLE documents
ADD CONSTRAINT documents_doc_id_chunk_idx_key
UNIQUE (doc_id, chunk_index);

-- If you have existing duplicates, first clean them up with:
-- DELETE FROM documents a USING documents b
-- WHERE a.id > b.id
-- AND a.doc_id = b.doc_id
-- AND a.chunk_index = b.chunk_index;
