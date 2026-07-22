# Week 2: End-to-End Local RAG Pipeline Implementation

**Goal:** Build and verify a complete vector ingestion and inference pipeline using PostgreSQL (`pgvector`), Ollama, and Python.

## 🛠️ Architecture & Components Built

1. **Vector Ingestion (`ingest.py`):**
   * Parsed enterprise security documentation into overlapping text chunks.
   * Leveraged Ollama's `nomic-embed-text` model to produce 768-dimensional embeddings.
   * Programmatically populated a PostgreSQL database with vector indices using `psycopg2` and `pgvector`.

2. **Grounded Inference (`query.py`):**
   * Transformed incoming user queries into mathematical embeddings.
   * Executed Cosine Distance queries (`<=>`) directly within PostgreSQL to retrieve top-k context matches.
   * Fed extracted enterprise context to a local LLM (`llama3`), enforcing zero-hallucination, context-grounded response generation.

## 💡 Architect Key Takeaway
By keeping document chunking, embedding generation, and vector search explicit, I verified the exact mathematical pathways required to securely query private enterprise data before adding higher-level orchestration abstractions.

---
*Next Phase: Transitioning from static RAG to dynamic Agentic Workflows (Phase 3).*