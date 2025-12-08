-- documents definition

CREATE TABLE documents (
	id TEXT(150) NOT NULL,
	chunk_type TEXT(250),
	chunk_index INTEGER,
	title TEXT,
	description TEXT,
	keywords TEXT,
	src TEXT, doc_id TEXT, chunk_text TEXT, embedding BLOB,
	CONSTRAINT documents_pk PRIMARY KEY (id)
);