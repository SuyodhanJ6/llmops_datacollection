from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # MongoDB connection settings
    MONGODB_URI: str
    DATABASE_NAME: str

    # Collection names
    USERS_COLLECTION: str = "users"
    ARTICLES_COLLECTION: str = "articles" 
    POSTS_COLLECTION: str = "posts"
    REPOSITORIES_COLLECTION: str = "repositories"
    
    # LinkedIn credentials 
    LINKEDIN_EMAIL: str | None = None
    LINKEDIN_PASSWORD: str | None = None
    
    # GitHub settings
    GITHUB_TOKEN: str | None = None
    
    # Browser settings
    BROWSER_TIMEOUT: int = 30
    SCROLL_LIMIT: int = 5
    
    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "protected_namespaces": ()  # Disable namespace warnings
    }

settings = Settings()