import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


class RAGChatBot:

    def __init__(self, model_name: str, rag_config: dict):
        self.model_name = model_name
        self.rag_config = rag_config
        self.initialize_model()

    def initialize_model(self):
        # Placeholder for model initialization logic
        # print(f"Initializing RAG model: {self.model_name} with config: {self.rag_config}")
        pass

    def chat(self, user_input: str) -> str:
        # Placeholder for chat logic
        print(f"User input: {user_input}")
        return "This is a response from the RAG model."


    def generate_llm_rag_response(self, prompt: str, documents: list) -> str:
        """
        Generate a response using the LLM and the provided documents.

        Args:
            prompt: The user prompt/question
            documents: List of relevant documents to use as context
        Returns:
            The generated response from the LLM
        """

        reponse = None

        return reponse

        # def generate_answer(self, query: str, documents: List[Document]) -> str:
        # """
        # Generate an answer using the LLM based on the query and found documents.
        # """
        # if not documents:
        #     return "No relevant documents found to answer the query."

        # # Create context from documents
        # context = "\n\n".join([
        #     f"Title: {doc.title}\nDescription: {doc.description}\nKeywords: {doc.keywords}"
        #     for doc in documents
        # ])

        # # Use the LLM to generate an answer
        # response = self.client.chat.completions.create(
        #     model="gpt-3.5-turbo",
        #     messages=[
        #         {"role": "system", "content": "You are a helpful assistant. Use the provided context to answer questions."},
        #         {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
        #     ]
        # )
        # return response.choices[0].message.content

    def search_docs(self, query_embedding: list[float], limit: int = 10) -> list:
        """
        Search documents using vector similarity with the query embedding.

        Args:
            query_embedding: The embedding vector to search with
            limit: Maximum number of documents to return (default: 10)

        Returns:
            List of dictionaries containing document information and similarity scores
        """

        if not query_embedding:
            return []

        # Database connection parameters
        dbname = os.environ.get("PG_DBNAME") or "postgres"
        dbuser = os.environ.get("POSTGRES_USER")
        dbpass = os.environ.get("POSTGRES_PASSWORD")
        pg_connection_string = f"dbname={dbname} user={dbuser} password={dbpass} host='0.0.0.0'"

        docs = []

        try:
            with psycopg2.connect(pg_connection_string) as conn:
                cur = conn.cursor()

                # SQL query using cosine similarity for vector search
                # The <=> operator computes cosine distance (1 - cosine similarity)
                # Lower distance means higher similarity
                sql_query = """
                SELECT id, title, description, keywords, 1 - (embedding <=> %s::vector) AS similarity_score
                FROM documents
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
                """

                # Execute the query with the embedding vector
                cur.execute(sql_query, (query_embedding, query_embedding, limit))

                # Fetch results and convert to list of dictionaries
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()

                for row in rows:
                    doc_dict = dict(zip(columns, row))
                    docs.append(doc_dict)

                cur.close()

        except Exception as e:
            print(f"Error searching documents: {e}")
            return []

        return docs
