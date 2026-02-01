from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://null_user@localhost:5432/null_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 3301

    # LLM Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    tavily_api_key: str = ""

    # Local LLM (Ollama)
    ollama_base_url: str = "http://localhost:11434"
    llm_provider: str = "ollama"  # "ollama" | "openai" | "anthropic"

    # Simulation defaults
    default_agents_per_faction: int = 5
    default_factions: int = 4
    ticks_per_epoch: int = 10
    max_budget_usd: float = 50.0

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
