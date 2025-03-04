from pydantic_settings import BaseSettings
from functools import lru_cache
from datetime import datetime
import os

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    
    # Application Settings
    app_name: str = "Professional Cocktail Advisor"
    debug: bool = False
    environment: str = "development"
    
    # Model Settings
    model_name: str = "gpt-3.5-turbo-16k"
    temperature: float = 0.7
    max_tokens: int = 800
    
    # Database Settings
    vector_db_path: str = "data/vector_store"
    redis_url: str = "redis://localhost:6379"
    postgres_url: str = "postgresql://user:password@localhost:5432/cocktails"
    
    # Rate Limiting
    rate_limit_requests: int = 60
    rate_limit_period: int = 60  # seconds
    
    # Cache Settings
    cache_ttl: int = 3600  # 1 hour
    
    # Security
    secret_key: str = "sk-xxxxxxxxxxxxxxxxxxxxxxxx"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Paths
    data_dir: str = "data"
    processed_data_dir: str = "data/processed"
    embeddings_dir: str = "data/processed/embeddings"
    
    # Application Constants
    MAX_RECOMMENDATIONS: int = 10
    MIN_SIMILARITY_SCORE: float = 0.7
    
    class Config:
        env_file = ".env"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def current_time(self) -> str:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()