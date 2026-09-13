import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AegisAI Sovereign Workbench"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "change-this-in-production-super-secret-sovereign-key"
    
    # DB
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "aegis_ai"
    POSTGRES_USER: str = "aegis_user"
    POSTGRES_PASSWORD: str = "aegis_secure_password"
    DATABASE_URL: str = "postgresql://aegis_user:aegis_secure_password@localhost:5432/aegis_ai"
    
    # Vector DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "aegis_documents"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Ollama Local LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_CHAT_MODEL: str = "qwen2.5:7b"
    DEFAULT_VISION_MODEL: str = "qwen2-vl:7b"
    DEFAULT_CODER_MODEL: str = "qwen2.5-coder:7b"
    
    # Air-Gap / Sovereign Controls
    EGRESS_MONITOR_ENABLED: bool = True
    CLASSIFICATION_TAG_DEFAULT: str = "INTERNAL"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
