"""Basic text cleaning and normalization utilities."""

import re
from typing import Any, Dict


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def strip_html_tags(text: str) -> str:
    """
    Strip potentially unsafe HTML tags (very basic implementation).
    
    TODO: Consider using a proper HTML sanitizer like bleach for production.
    
    Args:
        text: Input text potentially containing HTML
        
    Returns:
        Text with HTML tags removed
    """
    if not text:
        return ""
    
    # Remove HTML tags (basic regex - not comprehensive)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode common HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' ',
    }
    
    for entity, replacement in html_entities.items():
        text = text.replace(entity, replacement)
    
    return text


def clean_text(text: str, options: Dict[str, Any] | None = None) -> str:
    """
    Apply multiple cleaning operations to text.
    
    Args:
        text: Input text to clean
        options: Optional configuration for cleaning operations
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    options = options or {}
    
    # Strip HTML tags if requested (default: True)
    if options.get("strip_html", True):
        text = strip_html_tags(text)
    
    # Normalize whitespace if requested (default: True)
    if options.get("normalize_whitespace", True):
        text = normalize_whitespace(text)
    
    return text