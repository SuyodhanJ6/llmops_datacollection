class LLMOpsException(Exception):
    """Base exception for LLMOps data collection."""
    pass

class ImproperlyConfigured(LLMOpsException):
    """Exception raised when configuration is invalid."""
    pass

class CrawlerError(LLMOpsException):
    """Exception raised when crawler fails."""
    pass

class DatabaseError(LLMOpsException):
    """Exception raised when database operation fails."""
    pass

class ValidationError(LLMOpsException):
    """Exception raised when data validation fails."""
    pass