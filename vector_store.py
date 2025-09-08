"""
vector_store.py
---------------
Optimized semantic search, ranking, and agent selection for orchestrator.
"""

import os
import numpy as np
import psycopg2
from psycopg2 import pool
from typing import Dict, Any, List
import openai

# === Setup: Environment Variables & Connection Pool ===
PGVECTOR_CONN = os.getenv(
    "PGVECTOR_CONN",
    "dbname=orchestrator_db user=orchestrator_user password=orchestrator_pass host=localhost"
)
openai.api_key = os.getenv("OPENAI_API_KEY", "sk-...")

# Initialize connection pool
db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=5,
    dsn=PGVECTOR_CONN
)


# === Embedding Utilities ===
def get_embedding(text: str) -> List[float]:
    """Get embedding vector for text using OpenAI API (with caching potential)."""
    # Optional: Cache embeddings using Redis or a local store
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-3-small"  # faster & cheaper than ada-002
    )
    return response["data"][0]["embedding"]


# === Agent Vectorization ===
def batch_vectorize_agents(agent_records: List[Dict[str, Any]]):
    """
    Batch vectorize and update embeddings for agents.
    agent_records: [{"id": str, "name": str, "description": str, "capabilities": [...], "tags": [...], "reliability": float, "latency": float}]
    """
    conn = db_pool.getconn()
    cur = conn.cursor()
    try:
        for agent in agent_records:
            perf_str = f"Reliability: {agent['reliability']}, Latency: {agent['latency']}"
            text = f"Agent: {agent['name']}\nDescription: {agent['description']}\nCapabilities: {', '.join(agent['capabilities'])}\nTags: {', '.join(agent['tags'])}\n{perf_str}"
            embedding = get_embedding(text)
            cur.execute(
                "UPDATE agents SET embedding = %s WHERE id = %s",
                (embedding, agent['id'])
            )
        conn.commit()
    finally:
        cur.close()
        db_pool.putconn(conn)


# === Semantic Search ===
def semantic_search_agents(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Perform semantic search for agents using pgvector similarity search.
    """
    embedding = get_embedding(query)
    conn = db_pool.getconn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, name, description, capabilities, tags, reputation_score, reliability, avg_latency, embedding
            FROM agents
            WHERE embedding IS NOT NULL
            ORDER BY embedding <-> %s
            LIMIT %s
            """,
            (embedding, top_k)
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        db_pool.putconn(conn)

    agents = [
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "capabilities": row[3],
            "tags": row[4],
            "reputation_score": row[5],
            "reliability": row[6],
            "avg_latency": row[7],
            "embedding": row[8]
        }
        for row in rows
    ]
    return agents, embedding


# === Ranking ===
def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Fast cosine similarity."""
    a, b = np.array(vec_a), np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def rank_agents(agents: List[Dict[str, Any]], query_embedding: List[float]) -> List[Dict[str, Any]]:
    """Rank agents by semantic similarity + reliability + latency."""
    ranked = []
    for agent in agents:
        sim = cosine_similarity(query_embedding, agent["embedding"])
        reliability = agent.get("reliability", 0)
        latency = agent.get("avg_latency", 1000)
        score = sim * 0.6 + reliability * 0.3 + (1.0 / (latency + 1)) * 0.1
        agent["score"] = score
        ranked.append(agent)
    return sorted(ranked, key=lambda x: x["score"], reverse=True)


# === Orchestration Entry Point ===
def select_agents_for_intent(user_input: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Full selection pipeline."""
    agents, query_embedding = semantic_search_agents(user_input, top_k)
    return rank_agents(agents, query_embedding)


# === Future Placeholders ===
def classify_intent(user_input: str) -> str:
    """NLU intent classification placeholder."""
    return "general"

def graph_search(workflow_dag: Dict[str, Any], agents: List[Dict[str, Any]]) -> List[str]:
    """Placeholder for agent DAG optimization."""
    return list(workflow_dag.keys())
# Example usage:
# user_input = "Process customer orders and manage inventory."
# selected_agents = select_agents_for_intent(user_input, top_k=3)
# print(selected_agents)