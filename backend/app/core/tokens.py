"""Token counting utilities for text processing."""

import re
from typing import List


def rough_token_count(text: str) -> int:
    """
    Rough approximation of token count using whitespace tokenization.
    
    TODO: Replace with model-specific tokenizer (e.g., tiktoken for OpenAI models)
    when more precise token counting is needed.
    
    This is a naive approximation that:
    - Splits on whitespace
    - Counts punctuation as separate tokens
    - May overestimate actual token count
    
    Args:
        text: Input text to count tokens for
        
    Returns:
        Approximate token count
    """
    if not text or not text.strip():
        return 0
    
    # Split on whitespace and punctuation
    tokens = re.findall(r'\w+|[^\w\s]', text)
    return len(tokens)


def estimate_tokens_from_words(word_count: int) -> int:
    """
    Estimate token count from word count.
    
    Uses a rough approximation that 1 word ≈ 1.3 tokens on average
    for English text with OpenAI models.
    
    Args:
        word_count: Number of words
        
    Returns:
        Estimated token count
    """
    return int(word_count * 1.3)


def split_text_by_tokens(text: str, max_tokens: int) -> List[str]:
    """
    Split text into chunks with approximately max_tokens each.
    
    Args:
        text: Input text to split
        max_tokens: Maximum tokens per chunk
        
    Returns:
        List of text chunks
    """
    if not text or max_tokens <= 0:
        return []
    
    words = text.split()
    if not words:
        return []
    
    chunks = []
    current_chunk_words = []
    current_token_count = 0
    
    for word in words:
        word_tokens = rough_token_count(word)
        
        # If adding this word would exceed max_tokens, start new chunk
        if current_token_count + word_tokens > max_tokens and current_chunk_words:
            chunks.append(" ".join(current_chunk_words))
            current_chunk_words = []
            current_token_count = 0
        
        current_chunk_words.append(word)
        current_token_count += word_tokens
    
    # Add final chunk if it has content
    if current_chunk_words:
        chunks.append(" ".join(current_chunk_words))
    
    return chunks