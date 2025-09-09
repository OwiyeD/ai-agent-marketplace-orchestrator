from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str
    database_pool_size: int = 5
    database_max_overflow: int = 10
    
    # Redis
    redis_url: str
    redis_cache_url: str
    cache_ttl: int = 3600
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    debug: bool = False
    
    # Security
    secret_key: str
    cors_origins: list[str] = ["http://localhost:3000"]
    
    # Monitoring
    enable_metrics: bool = True
    prometheus_port: int = 9090
    log_level: str = "INFO"
    
    # LLM
    openai_api_key: Optional[str] = None
    llm_daily_budget: float = 50.0
    local_llm_endpoint: Optional[str] = None
    
    # Docker
    docker_timeout: int = 30
    docker_memory_limit: str = "512m"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()