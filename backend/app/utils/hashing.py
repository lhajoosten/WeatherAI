"""Hashing utilities for consistent key generation."""

import hashlib
from typing import List


def sha256_text(text: str) -> str:
    """
    Generate SHA256 hash of text.
    
    Args:
        text: Input text to hash
        
    Returns:
        Hexadecimal hash string
    """
    if not text:
        return ""
    
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_text_list(texts: List[str]) -> str:
    """
    Generate consistent hash of a list of texts.
    
    Ensures stable ordering by sorting texts before hashing.
    
    Args:
        texts: List of texts to hash
        
    Returns:
        Hexadecimal hash string
    """
    if not texts:
        return ""
    
    # Sort for consistent ordering
    sorted_texts = sorted(texts)
    
    # Create combined text with delimiter
    combined = "\n---\n".join(sorted_texts)
    
    return sha256_text(combined)


def create_cache_key(*parts: str, prefix: str = "") -> str:
    """
    Create a cache key from multiple parts.
    
    Args:
        *parts: String parts to combine
        prefix: Optional prefix for the key
        
    Returns:
        Cache key string
    """
    # Filter out empty parts
    valid_parts = [part for part in parts if part]
    
    if not valid_parts:
        return prefix if prefix else ""
    
    # Combine parts with delimiter
    combined = "|".join(valid_parts)
    
    # Hash the combined string for consistent length
    key_hash = sha256_text(combined)[:16]  # Use first 16 chars of hash
    
    if prefix:
        return f"{prefix}:{key_hash}"
    
    return key_hash