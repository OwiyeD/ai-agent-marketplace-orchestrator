# vector_store.py - Enhanced Agent Selection with Caching
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import redis
import pickle
import hashlib
from sqlalchemy.orm import Session
from database import SessionLocal, Agent
import logging

logger = logging.getLogger("vector_store")

class EnhancedVectorStore:
    """
    Enhanced vector store that integrates with your existing PostgreSQL agent storage
    while adding semantic search capabilities and caching.
    """
    
    def __init__(self, redis_client: redis.Redis, model_name: str = "all-MiniLM-L6-v2"):
        self.redis = redis_client
        self.model = SentenceTransformer(model_name)
        self.cache_ttl = 3600  # 1 hour
        
    def _get_cache_key(self, query: str, top_k: int) -> str:
        """Generate cache key for agent selection results"""
        key_string = f"agent_selection:{query}:{top_k}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_embedding_cache_key(self, text: str) -> str:
        """Generate cache key for text embeddings"""
        return f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding with caching"""
        cache_key = self._get_embedding_cache_key(text)
        
        # Try cache first
        cached_embedding = self.redis.get(cache_key)
        if cached_embedding:
            return pickle.loads(cached_embedding)
        
        # Generate new embedding
        embedding = self.model.encode(text)
        
        # Cache the embedding
        self.redis.setex(cache_key, self.cache_ttl, pickle.dumps(embedding))
        
        return embedding
    
    def _calculate_similarity(self, query_embedding: np.ndarray, agent_embedding: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        return np.dot(query_embedding, agent_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(agent_embedding)
        )
    
    def _get_agent_embedding_text(self, agent: Agent) -> str:
        """Create searchable text from agent attributes"""
        capabilities_text = " ".join(agent.capabilities) if agent.capabilities else ""
        return f"{agent.name} {agent.description} {capabilities_text}"
    
    def select_agents_for_intent(self, subtask: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Enhanced agent selection that combines your existing PostgreSQL search
        with semantic similarity and caching.
        """
        cache_key = self._get_cache_key(subtask, top_k)
        
        # Check cache first
        cached_result = self.redis.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for agent selection: {subtask}")
            return pickle.loads(cached_result)
        
        db = SessionLocal()
        try:
            # Get query embedding
            query_embedding = self.get_embedding(subtask)
            
            # Get all active agents from your existing database
            active_agents = db.query(Agent).filter(Agent.is_active == "active").all()
            
            if not active_agents:
                return []
            
            # Calculate similarities for all agents
            agent_scores = []
            for agent in active_agents:
                # Create agent text representation
                agent_text = self._get_agent_embedding_text(agent)
                agent_embedding = self.get_embedding(agent_text)
                
                # Calculate semantic similarity
                similarity = self._calculate_similarity(query_embedding, agent_embedding)
                
                # Combine with your existing reputation scoring
                # You mentioned hardcoded reputation scores of 100
                reputation_weight = 0.3
                similarity_weight = 0.7
                
                final_score = (similarity_weight * similarity + 
                              reputation_weight * (agent.reputation_score / 100))
                
                agent_scores.append({
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "endpoint_url": agent.endpoint_url,
                    "capabilities": agent.capabilities,
                    "reputation_score": agent.reputation_score,
                    "similarity_score": similarity,
                    "final_score": final_score,
                    "docker_image": f"agent-{agent.name.lower().replace(' ', '-')}"  # For sandbox
                })
            
            # Sort by final score and take top_k
            agent_scores.sort(key=lambda x: x["final_score"], reverse=True)
            top_agents = agent_scores[:top_k]
            
            # Cache the results
            self.redis.setex(cache_key, self.cache_ttl, pickle.dumps(top_agents))
            
            logger.info(f"Selected {len(top_agents)} agents for subtask: {subtask}")
            return top_agents
            
        finally:
            db.close()
    
    def update_agent_performance(self, agent_id: str, success: bool, response_time: float):
        """Update agent performance metrics for better future selection"""
        perf_key = f"agent_perf:{agent_id}"
        
        # Get existing performance data
        existing_data = self.redis.get(perf_key)
        if existing_data:
            perf_data = pickle.loads(existing_data)
        else:
            perf_data = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "avg_response_time": 0.0,
                "success_rate": 0.0
            }
        
        # Update metrics
        perf_data["total_tasks"] += 1
        if success:
            perf_data["successful_tasks"] += 1
        
        # Update average response time (exponential moving average)
        alpha = 0.1  # Smoothing factor
        perf_data["avg_response_time"] = (
            alpha * response_time + 
            (1 - alpha) * perf_data["avg_response_time"]
        )
        
        # Calculate success rate
        perf_data["success_rate"] = (
            perf_data["successful_tasks"] / perf_data["total_tasks"]
        )
        
        # Cache updated performance data
        self.redis.setex(perf_key, self.cache_ttl * 24, pickle.dumps(perf_data))  # 24 hour TTL
        
        logger.info(f"Updated performance for agent {agent_id}: "
                   f"success_rate={perf_data['success_rate']:.2f}")

# Backwards compatibility function for your existing code
def select_agents_for_intent(subtask: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Backwards compatible function that uses enhanced vector store"""
    redis_client = redis.Redis.from_url("redis://localhost:6379/1")
    vector_store = EnhancedVectorStore(redis_client)
    return vector_store.select_agents_for_intent(subtask, top_k)