import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    PROJECT_NAME: str = "AegisAI Sovereign Workbench"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    ALLOW_DEVELOPMENT_IDENTITY_FALLBACK: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "change-this-in-production-super-secret-sovereign-key"
    
    # DB
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "aegis_ai"
    POSTGRES_USER: str = "aegis_user"
    POSTGRES_PASSWORD: str = "aegis_secure_password"
    DATABASE_URL: str = "postgresql://aegis_user:aegis_secure_password@localhost:5432/aegis_ai"
    
    # Vector DB - Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "industrial_docs"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Ollama Local LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    AEGIS_MODEL_GENERAL: str = "qwen2.5:3b"
    AEGIS_MODEL_CODING: str = "qwen2.5-coder:3b"
    AEGIS_MODEL_VISION: str = ""
    AEGIS_MODEL_EMBEDDINGS: str = "BAAI/bge-small-en-v1.5"
    DEFAULT_CHAT_MODEL: str = AEGIS_MODEL_GENERAL
    DEFAULT_VISION_MODEL: str = AEGIS_MODEL_VISION
    DEFAULT_CODER_MODEL: str = AEGIS_MODEL_CODING
    
    # Final hybrid-RAG stack for the Aegis AI design.
    DENSE_EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    SPARSE_EMBEDDING_MODEL: str = "Qdrant/bm25"
    RERANKER_MODEL: str = "BAAI/bge-reranker-base"
    
    # RAG Configuration
    CHUNK_SIZE_TOKENS: int = 400
    CHUNK_OVERLAP_TOKENS: int = 50
    TOP_K_RETRIEVE: int = 5  # Final top-k after reranking
    TOP_K_PREFETCH: int = 20  # Prefetch before fusion/reranking
    
    # Air-Gap / Sovereign Controls
    EGRESS_MONITOR_ENABLED: bool = True
    EGRESS_ENFORCE: bool = True
    EGRESS_ALLOW_HOSTS: str = ""
    CLASSIFICATION_TAG_DEFAULT: str = "INTERNAL"
    SANDBOX_URL: str = ""
    SANDBOX_TIMEOUT_SECONDS: float = 5.0
    SANDBOX_MEMORY_MB: int = 256
    SANDBOX_CPU_LIMIT: float = 0.5
    SANDBOX_MAX_OUTPUT_BYTES: int = 65536
    SANDBOX_MAX_INPUT_BYTES: int = 32768
    SANDBOX_ALLOW_LOCAL_FALLBACK: bool = True
    ARTIFACT_STORAGE_DIR: str = "artifacts"

settings = Settings()
