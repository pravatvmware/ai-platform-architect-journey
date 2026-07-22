import requests
import psycopg2
from pgvector.psycopg2 import register_vector

# --- Configuration Constants ---
DB_CONFIG = {
    "dbname": "rag_database",
    "user": "rag_admin",
    "password": "enterprise_secure_password",
    "host": "127.0.0.1",
    "port": "5433"
}

OLLAMA_API_URL = "http://localhost:11434/api"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3"

def get_embedding(text: str) -> list[float]:
    """Converts the user's question into a mathematical vector."""
    response = requests.post(
        f"{OLLAMA_API_URL}/embeddings",
        json={"model": EMBEDDING_MODEL, "prompt": text}
    )
    response.raise_for_status()
    return response.json()["embedding"]

def retrieve_context(question_embedding: list[float], limit: int = 2) -> str:
    """Searches PostgreSQL for the most relevant document chunks."""
    conn = psycopg2.connect(**DB_CONFIG)
    register_vector(conn)
    cursor = conn.cursor()
    
    # The <=> operator calculates Cosine Distance in pgvector
    cursor.execute("""
        SELECT content 
        FROM enterprise_embeddings 
        ORDER BY embedding <=> %s::vector 
        LIMIT %s
    """, (question_embedding, limit))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Combine the top results into a single text block
    return "\n\n".join([row[0] for row in results])

def generate_answer(question: str, context: str) -> str:
    """Passes the context and question to the LLM for a grounded answer."""
    prompt = f"""You are an Enterprise AI Architect assistant. Answer the question based strictly on the provided context. 

Context:
{context}

Question:
{question}

Answer:"""

    response = requests.post(
        f"{OLLAMA_API_URL}/generate",
        json={"model": LLM_MODEL, "prompt": prompt, "stream": False}
    )
    response.raise_for_status()
    return response.json()["response"]

def main():
    print("🚀 Initializing Inference Pipeline...\n")
    
    # The question we want to ask our internal documentation
    question = "What are the guardrails for autonomous AI agents?"
    print(f"❓ Question: {question}\n")
    
    print("⚡ 1. Generating embedding for the question...")
    question_embedding = get_embedding(question)
    
    print("🔍 2. Searching Postgres for enterprise context...")
    context = retrieve_context(question_embedding)
    print(f"📄 Found relevant context:\n---\n{context}\n---\n")
    
    print("🧠 3. Generating grounded answer using LLM...")
    answer = generate_answer(question, context)
    
    print(f"✨ Final Answer:\n{answer}")

if __name__ == "__main__":
    main()