import os
import json
import requests
import psycopg2
from pgvector.psycopg2 import register_vector

# --- Configuration Constants ---
DB_CONFIG = {
    "dbname": "rag_database",
    "user": "rag_admin",       # Updated user
    "password": "enterprise_secure_password",
    "host": "127.0.0.1",
    "port": "5433"             # Updated port
}

OLLAMA_API_URL = "http://localhost:11434/api/embeddings"
EMBEDDING_MODEL = "nomic-embed-text"
VECTOR_DIMENSION = 768  # nomic-embed-text outputs 768-dim vectors


def get_embedding(text: str) -> list[float]:
    """Calls Ollama API to produce vector embeddings for a text string."""
    response = requests.post(
        OLLAMA_API_URL,
        json={"model": EMBEDDING_MODEL, "prompt": text}
    )
    response.raise_for_status()
    return response.json()["embedding"]


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """Splits a document into overlapping text chunks for optimal RAG context retrieval."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def setup_database_schema(cursor):
    """Ensures vector extension and target vector table exist."""
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS enterprise_embeddings (
            id SERIAL PRIMARY KEY,
            document_name VARCHAR(255),
            chunk_index INT,
            content TEXT,
            embedding vector({VECTOR_DIMENSION}),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)


def main():
    print("🚀 Initializing Ingestion Pipeline...")
    
    # Connect to PostgreSQL container
    conn = psycopg2.connect(**DB_CONFIG)
    register_vector(conn)
    cursor = conn.cursor()
    
    # 1. Initialize DB Schema
    setup_database_schema(cursor)
    conn.commit()
    print("✅ Database schema verified.")

    # 2. Read Source Document
    doc_path = os.path.join(os.path.dirname(__file__), "data", "sample_policy.txt")
    if not os.path.exists(doc_path):
        print(f"❌ Error: Sample document not found at {doc_path}")
        return

    with open(doc_path, "r", encoding="utf-8") as f:
        document_text = f.read()

    # 3. Chunk Document
    chunks = chunk_text(document_text)
    print(f"📄 Created {len(chunks)} chunks from source document.")

    # 4. Generate Embeddings & Ingest into Postgres
    for idx, chunk in enumerate(chunks):
        print(f"  ⚡ Generating embedding for chunk {idx + 1}/{len(chunks)}...")
        embedding = get_embedding(chunk)
        
        cursor.execute("""
            INSERT INTO enterprise_embeddings (document_name, chunk_index, content, embedding)
            VALUES (%s, %s, %s, %s)
        """, ("sample_policy.txt", idx, chunk, embedding))

    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n✨ Ingestion complete! Data successfully vector-indexed into PostgreSQL.")


if __name__ == "__main__":
    main()