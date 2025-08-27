"""
Sample data for testing the pydantic-ai vector database example.
"""

from typing import List, Dict, Any


def get_sample_documents() -> List[Dict[str, Any]]:
    """
    Get a collection of sample documents for testing the vector database.

    Returns:
        List of document dictionaries with title, content, and metadata
    """
    documents = [
        {
            "id": "doc_1",
            "title": "Introduction to Machine Learning",
            "content": """
            Machine learning is a subset of artificial intelligence that focuses on the development of algorithms
            and statistical models that enable computer systems to improve their performance on a specific task
            through experience. Unlike traditional programming where explicit instructions are provided, machine
            learning systems learn patterns from data to make predictions or decisions. The three main types of
            machine learning are supervised learning, unsupervised learning, and reinforcement learning.
            Supervised learning uses labeled data to train models, unsupervised learning finds patterns in
            unlabeled data, and reinforcement learning learns through interaction with an environment.
            """.strip(),
            "metadata": {
                "category": "AI/ML",
                "difficulty": "beginner",
                "tags": ["machine learning", "artificial intelligence", "algorithms"],
            },
        },
        {
            "id": "doc_2",
            "title": "Python Data Structures",
            "content": """
            Python provides several built-in data structures that are essential for programming. Lists are ordered,
            mutable collections that can store items of different types. Tuples are ordered, immutable collections
            that are often used for data that shouldn't change. Dictionaries are unordered collections of key-value
            pairs that provide fast lookup times. Sets are unordered collections of unique elements that support
            mathematical set operations like union and intersection. Understanding when to use each data structure
            is crucial for writing efficient Python code. Lists are great for sequences that need to be modified,
            tuples for fixed data, dictionaries for mappings, and sets for unique collections.
            """.strip(),
            "metadata": {
                "category": "Programming",
                "difficulty": "beginner",
                "tags": ["python", "data structures", "programming"],
            },
        },
        {
            "id": "doc_3",
            "title": "Vector Databases and Embeddings",
            "content": """
            Vector databases are specialized databases designed to store and query high-dimensional vector data,
            typically used in machine learning applications. These databases excel at similarity search, where
            you want to find vectors that are similar to a query vector. Embeddings are dense vector representations
            of data like text, images, or audio that capture semantic meaning. Popular vector databases include
            Pinecone, Weaviate, Chroma, and Qdrant. They use techniques like approximate nearest neighbor (ANN)
            search to efficiently find similar vectors even in high-dimensional spaces. Vector databases are
            essential for applications like recommendation systems, semantic search, and retrieval-augmented
            generation (RAG) systems.
            """.strip(),
            "metadata": {
                "category": "Database",
                "difficulty": "intermediate",
                "tags": ["vector database", "embeddings", "similarity search", "RAG"],
            },
        },
        {
            "id": "doc_4",
            "title": "RESTful API Design Principles",
            "content": """
            REST (Representational State Transfer) is an architectural style for designing web APIs. RESTful APIs
            follow several key principles: they are stateless, meaning each request contains all necessary information;
            they use standard HTTP methods (GET, POST, PUT, DELETE) appropriately; they have a uniform interface with
            consistent URL patterns; and they are cacheable to improve performance. Good RESTful API design includes
            using nouns for resources (not verbs), implementing proper HTTP status codes, versioning your API, and
            providing clear documentation. Security considerations include authentication, authorization, and input
            validation. Modern APIs often include features like pagination, filtering, and rate limiting.
            """.strip(),
            "metadata": {
                "category": "Web Development",
                "difficulty": "intermediate",
                "tags": ["REST", "API", "web development", "HTTP"],
            },
        },
        {
            "id": "doc_5",
            "title": "Database Normalization",
            "content": """
            Database normalization is the process of organizing data in a database to reduce redundancy and improve
            data integrity. The normal forms (1NF, 2NF, 3NF, BCNF) provide guidelines for structuring tables.
            First Normal Form (1NF) requires that each column contains atomic values and each record is unique.
            Second Normal Form (2NF) builds on 1NF by ensuring that non-key attributes are fully dependent on the
            primary key. Third Normal Form (3NF) eliminates transitive dependencies where non-key attributes depend
            on other non-key attributes. While normalization reduces redundancy, it can sometimes impact query
            performance, leading to the strategic use of denormalization in certain scenarios.
            """.strip(),
            "metadata": {
                "category": "Database",
                "difficulty": "intermediate",
                "tags": ["database", "normalization", "data modeling", "SQL"],
            },
        },
        {
            "id": "doc_6",
            "title": "Microservices Architecture",
            "content": """
            Microservices architecture is a design approach where applications are built as a collection of small,
            independent services that communicate over well-defined APIs. Each microservice is responsible for a
            specific business function and can be developed, deployed, and scaled independently. Benefits include
            improved scalability, technology diversity, fault isolation, and faster development cycles. However,
            microservices also introduce complexity in terms of service discovery, distributed data management,
            network communication, and monitoring. Key patterns include API gateways, circuit breakers, and
            distributed tracing. Container technologies like Docker and orchestration platforms like Kubernetes
            are commonly used to deploy and manage microservices.
            """.strip(),
            "metadata": {
                "category": "Architecture",
                "difficulty": "advanced",
                "tags": [
                    "microservices",
                    "architecture",
                    "distributed systems",
                    "containers",
                ],
            },
        },
        {
            "id": "doc_7",
            "title": "Git Version Control Basics",
            "content": """
            Git is a distributed version control system that tracks changes in source code during software development.
            Key concepts include repositories (repos), commits, branches, and merges. A repository contains the entire
            history of a project. Commits are snapshots of changes with descriptive messages. Branches allow parallel
            development of features without affecting the main codebase. Common Git commands include git init, git add,
            git commit, git push, git pull, and git merge. Best practices include writing clear commit messages, using
            branching strategies like Git Flow, and regularly pulling changes from remote repositories. Understanding
            Git is essential for collaborative software development and maintaining code history.
            """.strip(),
            "metadata": {
                "category": "Development Tools",
                "difficulty": "beginner",
                "tags": ["git", "version control", "development", "collaboration"],
            },
        },
        {
            "id": "doc_8",
            "title": "Cloud Computing Fundamentals",
            "content": """
            Cloud computing delivers computing services over the internet, including servers, storage, databases,
            networking, software, and analytics. The three main service models are Infrastructure as a Service (IaaS),
            Platform as a Service (PaaS), and Software as a Service (SaaS). Deployment models include public, private,
            hybrid, and multi-cloud. Major cloud providers include Amazon Web Services (AWS), Microsoft Azure, and
            Google Cloud Platform (GCP). Benefits of cloud computing include cost efficiency, scalability, reliability,
            and global reach. Key considerations include security, compliance, vendor lock-in, and data governance.
            Cloud-native technologies like containers, serverless computing, and managed services are transforming
            how applications are built and deployed.
            """.strip(),
            "metadata": {
                "category": "Cloud Computing",
                "difficulty": "intermediate",
                "tags": ["cloud", "AWS", "Azure", "infrastructure", "scalability"],
            },
        },
    ]

    return documents


def get_sample_queries() -> List[str]:
    """
    Get a list of sample queries for testing the RAG system.

    Returns:
        List of sample query strings
    """
    queries = [
        "What is machine learning?",
        "How do Python data structures work?",
        "Tell me about vector databases",
        "What are the principles of REST API design?",
        "Explain database normalization",
        "What are microservices?",
        "How does Git version control work?",
        "What is cloud computing?",
        "What are embeddings used for?",
        "How do you design scalable systems?",
        "What's the difference between supervised and unsupervised learning?",
        "Which Python data structure should I use for unique items?",
        "How do vector databases perform similarity search?",
        "What HTTP methods are used in REST APIs?",
        "What is the purpose of database normalization?",
    ]

    return queries


def get_sample_metadata_filters() -> List[Dict[str, Any]]:
    """
    Get sample metadata filters for testing filtered searches.

    Returns:
        List of metadata filter dictionaries
    """
    filters = [
        {"category": "AI/ML"},
        {"category": "Programming"},
        {"difficulty": "beginner"},
        {"difficulty": "intermediate"},
        {"difficulty": "advanced"},
        {"tags": ["python"]},
        {"tags": ["database"]},
        {"category": "Web Development", "difficulty": "intermediate"},
    ]

    return filters
