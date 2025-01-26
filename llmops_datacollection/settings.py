from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # MongoDB settings
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "llmops_data"
    
    # LinkedIn credentials
    LINKEDIN_EMAIL: str | None = None
    LINKEDIN_PASSWORD: str | None = None
    
    # Optional GitHub token (for private repos)
    GITHUB_TOKEN: str | None = None
    
    # Browser settings
    BROWSER_TIMEOUT: int = 30
    SCROLL_LIMIT: int = 5
    
    # Logging
    LOG_LEVEL: str = "INFO"

settings = Settings()