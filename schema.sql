CREATE EXTENSION IF NOT EXISTS vector;

-- Create your table
CREATE table if not exists documents (
    id SERIAL PRIMARY KEY,
    title TEXT,
    description TEXT,
    keywords TEXT[],
    authors TEXT[],
    chunk_text TEXT,
    chunk_index INTEGER,
    embedding vector(384), -- Adjust dimension based on your embedding model
    created_at TIMESTAMP DEFAULT NOW(),
    doc_id varchar(255),
    chunk_type varchar(255),
    data_source varchar(75)
);