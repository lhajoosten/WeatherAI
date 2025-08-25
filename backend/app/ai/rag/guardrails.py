"""Guardrails and safety checks for RAG pipeline."""

import re
from typing import List
import structlog

from .models import RetrievedChunk
from .exceptions import LowSimilarityError

logger = structlog.get_logger(__name__)


def check_similarity_threshold(
    chunks: List[RetrievedChunk], 
    threshold: float
) -> List[RetrievedChunk]:
    """
    Check that retrieved chunks meet similarity threshold.
    
    Args:
        chunks: List of retrieved chunks with scores
        threshold: Minimum similarity threshold
        
    Returns:
        Filtered list of chunks above threshold
        
    Raises:
        LowSimilarityError: If all chunks are below threshold
    """
    if not chunks:
        raise LowSimilarityError(threshold=threshold, max_similarity=0.0)
    
    filtered_chunks = [chunk for chunk in chunks if chunk.score >= threshold]
    
    if not filtered_chunks:
        max_score = max(chunk.score for chunk in chunks)
        logger.warning(
            "All chunks below similarity threshold",
            threshold=threshold,
            max_score=max_score,
            num_chunks=len(chunks)
        )
        raise LowSimilarityError(threshold=threshold, max_similarity=max_score)
    
    return filtered_chunks


def sanitize_user_query(query: str) -> str:
    """
    Sanitize user query to prevent prompt injection and other issues.
    
    This is a basic implementation. For production, consider more sophisticated
    prompt injection detection methods.
    
    Args:
        query: Raw user query
        
    Returns:
        Sanitized query
    """
    if not query:
        return ""
    
    # Remove potential system instruction patterns
    query = re.sub(r'(?i)system\s*:', '', query)
    query = re.sub(r'(?i)assistant\s*:', '', query)
    query = re.sub(r'(?i)user\s*:', '', query)
    
    # Remove markdown-style instruction patterns
    query = re.sub(r'#\s*instructions?\s*:', '', query, flags=re.IGNORECASE)
    query = re.sub(r'#\s*system\s*:', '', query, flags=re.IGNORECASE)
    
    # Remove potential role-playing instructions
    query = re.sub(r'(?i)ignore\s+(?:previous|all)\s+instructions?', '', query)
    query = re.sub(r'(?i)you\s+are\s+now\s+', '', query)
    query = re.sub(r'(?i)act\s+as\s+', '', query)
    query = re.sub(r'(?i)pretend\s+(?:to\s+be|you\s+are)', '', query)
    
    # Remove excessive whitespace
    query = re.sub(r'\s+', ' ', query)
    query = query.strip()
    
    # Limit length to prevent extremely long queries
    max_length = 1000
    if len(query) > max_length:
        logger.warning(
            "Query truncated due to length",
            original_length=len(query),
            max_length=max_length
        )
        query = query[:max_length].rsplit(' ', 1)[0]  # Break at word boundary
    
    return query


def validate_content_safety(content: str) -> bool:
    """
    Basic content safety validation.
    
    TODO: Integrate with proper content moderation service for production.
    
    Args:
        content: Content to validate
        
    Returns:
        True if content appears safe, False otherwise
    """
    if not content:
        return True
    
    # Basic pattern matching for obviously problematic content
    # This is a very basic implementation
    
    dangerous_patterns = [
        r'(?i)\b(?:kill|murder|bomb|terrorist|violence)\b',
        r'(?i)\b(?:hack|crack|exploit|malware)\b',
        r'(?i)\b(?:illegal|drugs|weapons)\b',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, content):
            logger.warning(
                "Content flagged by safety check",
                pattern=pattern,
                content_preview=content[:100]
            )
            return False
    
    return True


def check_context_quality(chunks: List[RetrievedChunk]) -> dict:
    """
    Assess the quality of retrieved context.
    
    Args:
        chunks: List of retrieved chunks
        
    Returns:
        Dictionary with quality metrics
    """
    if not chunks:
        return {
            "quality_score": 0.0,
            "num_chunks": 0,
            "avg_similarity": 0.0,
            "min_similarity": 0.0,
            "max_similarity": 0.0,
            "content_diversity": 0.0
        }
    
    # Calculate similarity metrics
    similarities = [chunk.score for chunk in chunks]
    avg_similarity = sum(similarities) / len(similarities)
    min_similarity = min(similarities)
    max_similarity = max(similarities)
    
    # Calculate content diversity (simple Jaccard-based approach)
    content_diversity = _calculate_content_diversity(chunks)
    
    # Overall quality score (weighted combination)
    quality_score = (
        0.4 * avg_similarity +  # Average relevance
        0.3 * min_similarity +  # Minimum acceptable relevance
        0.3 * content_diversity  # Diversity bonus
    )
    
    return {
        "quality_score": quality_score,
        "num_chunks": len(chunks),
        "avg_similarity": avg_similarity,
        "min_similarity": min_similarity,
        "max_similarity": max_similarity,
        "content_diversity": content_diversity
    }


def _calculate_content_diversity(chunks: List[RetrievedChunk]) -> float:
    """
    Calculate diversity score for content chunks.
    
    Uses pairwise Jaccard similarity to measure how different the chunks are.
    Higher diversity is better for comprehensive answers.
    
    Args:
        chunks: List of retrieved chunks
        
    Returns:
        Diversity score between 0 and 1 (higher = more diverse)
    """
    if len(chunks) <= 1:
        return 1.0  # Single chunk is perfectly "diverse"
    
    # Calculate pairwise Jaccard similarities
    similarities = []
    
    for i in range(len(chunks)):
        for j in range(i + 1, len(chunks)):
            similarity = _jaccard_similarity(
                chunks[i].chunk.content,
                chunks[j].chunk.content
            )
            similarities.append(similarity)
    
    if not similarities:
        return 1.0
    
    # Diversity is inverse of average similarity
    avg_similarity = sum(similarities) / len(similarities)
    diversity = 1.0 - avg_similarity
    
    return max(0.0, min(1.0, diversity))  # Clamp to [0, 1]


def _jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between two texts as word sets."""
    if not text1 or not text2:
        return 0.0
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0