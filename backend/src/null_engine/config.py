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
    default_agents_per_faction: int = 3
    default_factions: int = 3
    ticks_per_epoch: int = 10
    max_budget_usd: float = 50.0

    # Ops alert thresholds
    ops_runner_ticks_min_for_alert: int = 10
    ops_runner_success_rate_threshold: float = 0.9
    ops_translator_backlog_threshold: int = 50
    ops_generating_worlds_threshold: int = 5

    # Vector DB behavior
    # When false, app falls back to JSON columns if pgvector extension is unavailable.
    pgvector_required: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
