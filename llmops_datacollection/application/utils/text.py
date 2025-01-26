import re
from typing import Tuple

def clean_text(text: str) -> str:
    """Clean text by removing special characters and extra whitespace."""
    # Remove special characters but keep basic punctuation
    text = re.sub(r"[^\w\s.,!?]", " ", text)
    
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    
    return text.strip()

def split_full_name(full_name: str) -> Tuple[str, str]:
    """Split full name into first and last name."""
    parts = full_name.strip().split()
    if len(parts) < 2:
        raise ValueError("Full name must include first and last name")
        
    return " ".join(parts[:-1]), parts[-1]

def extract_urls(text: str) -> list[str]:
    """Extract URLs from text."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)

def normalize_url(url: str) -> str:
    """Normalize URL by removing trailing slashes and query parameters."""
    url = url.split("?")[0]  # Remove query parameters
    return url.rstrip("/")   # Remove trailing slashes