"""
Complete working example of pydantic-ai with vector database querying.

This example demonstrates:
1. Setting up a vector database with sample documents
2. Using pydantic-ai agents to query the database
3. Generating structured responses with source citations
4. Both full AI agent and simplified implementations
"""

import asyncio
import time
from typing import Optional

from models import ChatQuery, SearchQuery
from vector_store import SimpleVectorStore
from agent import RAGAgent, SimpleRAGAgent
from sample_data import get_sample_documents, get_sample_queries


def setup_vector_store() -> SimpleVectorStore:
    """
    Set up the vector store with sample documents.

    Returns:
        Initialized vector store with sample data
    """
    print("🔧 Setting up vector store...")

    # Initialize vector store
    vector_store = SimpleVectorStore(model_name="all-MiniLM-L6-v2")

    # Load sample documents
    documents = get_sample_documents()
    print(f"📚 Loading {len(documents)} sample documents...")

    # Add documents to vector store
    doc_ids = vector_store.add_documents(documents)
    print(f"✅ Added {len(doc_ids)} documents to vector store")

    # Display stats
    stats = vector_store.get_stats()
    print(f"📊 Vector store stats:")
    print(f"   - Total documents: {stats.total_documents}")
    print(f"   - Embedding dimension: {stats.embedding_dimension}")
    print(f"   - Index size: {stats.index_size_mb:.2f} MB")

    return vector_store


def demonstrate_vector_search(vector_store: SimpleVectorStore):
    """
    Demonstrate basic vector search functionality.

    Args:
        vector_store: The initialized vector store
    """
    print("\n🔍 Demonstrating vector search...")

    # Test queries
    test_queries = [
        "machine learning algorithms",
        "Python programming",
        "database design",
    ]

    for query_text in test_queries:
        print(f"\n🔎 Searching for: '{query_text}'")

        # Create search query
        query = SearchQuery(query=query_text, top_k=3, threshold=0.1)

        # Perform search
        start_time = time.time()
        response = vector_store.search(query)
        search_time = (time.time() - start_time) * 1000

        print(f"⏱️  Search completed in {search_time:.2f}ms")
        print(f"📋 Found {response.total_results} results:")

        for result in response.results:
            print(f"   {result.rank}. {result.document.title}")
            print(f"      Similarity: {result.similarity_score:.3f}")
            print(f"      Category: {result.document.metadata.get('category', 'N/A')}")


async def demonstrate_rag_agent(vector_store: SimpleVectorStore):
    """
    Demonstrate the full pydantic-ai RAG agent.

    Args:
        vector_store: The initialized vector store
    """
    print("\n🤖 Demonstrating pydantic-ai RAG agent...")

    # Initialize RAG agent
    # Note: You'll need to set your OpenAI API key for this to work
    # You can also use other models supported by pydantic-ai
    try:
        rag_agent = RAGAgent(vector_store)

        # Test queries
        test_queries = [
            "What is machine learning and how does it work?",
            "Which Python data structure should I use for storing unique items?",
            "How do vector databases perform similarity search?",
        ]

        for query_text in test_queries:
            print(f"\n💬 Query: '{query_text}'")

            # Create chat query
            chat_query = ChatQuery(
                message=query_text, context_limit=3, include_sources=True
            )

            # Get response from agent
            try:
                response = await rag_agent.chat(chat_query)

                print(f"🤖 Response: {response.response}")
                print(f"🎯 Confidence: {response.confidence:.2f}")
                print(f"⏱️  Processing time: {response.processing_time_ms:.2f}ms")

                if response.sources:
                    print(f"📚 Sources ({len(response.sources)}):")
                    for source in response.sources:
                        print(
                            f"   - {source.document.title} (similarity: {source.similarity_score:.3f})"
                        )

            except Exception as e:
                print(f"❌ Error with AI agent: {e}")
                print("💡 This might be due to missing API keys or model configuration")

    except Exception as e:
        print(f"❌ Could not initialize RAG agent: {e}")
        print("💡 This might be due to missing API keys or model configuration")


def demonstrate_simple_rag_agent(vector_store: SimpleVectorStore):
    """
    Demonstrate the simplified RAG agent (no external AI model required).

    Args:
        vector_store: The initialized vector store
    """
    print("\n🔧 Demonstrating simple RAG agent (no external AI required)...")

    # Initialize simple RAG agent
    simple_agent = SimpleRAGAgent(vector_store)

    # Test queries
    test_queries = [
        "What is machine learning?",
        "Tell me about Python data structures",
        "How do vector databases work?",
    ]

    for query_text in test_queries:
        print(f"\n💬 Query: '{query_text}'")

        # Get response from simple agent
        response = simple_agent.chat(query_text, context_limit=2)

        print(f"🤖 Response: {response.response}")
        print(f"🎯 Confidence: {response.confidence:.2f}")
        print(f"⏱️  Processing time: {response.processing_time_ms:.2f}ms")

        if response.sources:
            print(f"📚 Sources ({len(response.sources)}):")
            for source in response.sources:
                print(
                    f"   - {source.document.title} (similarity: {source.similarity_score:.3f})"
                )


def interactive_demo(vector_store: SimpleVectorStore):
    """
    Interactive demo where users can ask questions.

    Args:
        vector_store: The initialized vector store
    """
    print("\n🎮 Interactive Demo")
    print("Ask questions about the topics in the database!")
    print(
        "Topics include: Machine Learning, Python, Databases, APIs, Git, Cloud Computing, etc."
    )
    print("Type 'quit' to exit.\n")

    # Use simple agent for interactive demo (no API keys required)
    simple_agent = SimpleRAGAgent(vector_store)

    while True:
        try:
            query = input("❓ Your question: ").strip()

            if query.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break

            if not query:
                continue

            print("🔍 Searching...")
            response = simple_agent.chat(query, context_limit=3)

            print(f"\n🤖 Answer: {response.response}")
            print(f"🎯 Confidence: {response.confidence:.2f}")

            if response.sources:
                print(f"\n📚 Sources:")
                for i, source in enumerate(response.sources, 1):
                    print(f"   {i}. {source.document.title}")
                    print(
                        f"      Category: {source.document.metadata.get('category', 'N/A')}"
                    )
                    print(f"      Similarity: {source.similarity_score:.3f}")

            print("-" * 50)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Main function that runs all demonstrations."""
    print("🚀 Pydantic-AI Vector Database Example")
    print("=" * 50)

    # Setup
    vector_store = setup_vector_store()

    # Demonstrate vector search
    demonstrate_vector_search(vector_store)

    # Demonstrate simple RAG agent (always works)
    demonstrate_simple_rag_agent(vector_store)

    # Demonstrate full pydantic-ai agent (requires API keys)
    await demonstrate_rag_agent(vector_store)

    # Interactive demo
    print("\n" + "=" * 50)
    interactive_demo(vector_store)


if __name__ == "__main__":
    # Run the main demonstration
    asyncio.run(main())
