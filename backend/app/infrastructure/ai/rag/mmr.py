"""Maximum Marginal Relevance (MMR) algorithm implementation."""

import numpy as np
from typing import List

from .models import RetrievedChunk


def apply_mmr(
    candidates: List[RetrievedChunk],
    query_vector: List[float],
    top_k: int,
    lambda_mult: float = 0.5
) -> List[RetrievedChunk]:
    """
    Apply Maximum Marginal Relevance re-ranking to retrieved chunks.
    
    MMR balances relevance to the query with diversity among selected documents.
    The algorithm iteratively selects documents that maximize:
    MMR = λ * Sim(D_i, Q) - (1-λ) * max_j Sim(D_i, D_j)
    
    Where:
    - λ (lambda_mult) controls the trade-off between relevance and diversity
    - Sim(D_i, Q) is the similarity between document i and the query
    - max_j Sim(D_i, D_j) is the maximum similarity between document i and any already selected document
    
    Args:
        candidates: List of retrieved chunks with similarity scores
        query_vector: Original query embedding vector
        top_k: Maximum number of documents to select
        lambda_mult: Trade-off parameter (0 = max diversity, 1 = max relevance)
        
    Returns:
        Re-ranked list of chunks according to MMR
    """
    if not candidates or top_k <= 0:
        return []
    
    # If we have fewer candidates than requested, return all
    if len(candidates) <= top_k:
        return candidates
    
    # Extract embeddings - we'll need to recalculate them from the vector store
    # For now, use the similarity scores as approximation
    # TODO: Store embeddings with chunks for proper MMR calculation
    
    selected = []
    remaining = candidates.copy()
    
    # First selection: highest relevance score
    first_idx = 0
    max_score = remaining[0].score
    for i, chunk in enumerate(remaining):
        if chunk.score > max_score:
            max_score = chunk.score
            first_idx = i
    
    selected.append(remaining.pop(first_idx))
    
    # Iteratively select remaining documents
    while len(selected) < top_k and remaining:
        best_idx = -1
        best_mmr_score = float('-inf')
        
        for i, candidate in enumerate(remaining):
            # Relevance component: original similarity to query
            relevance = candidate.score
            
            # Diversity component: maximum similarity to already selected docs
            # Since we don't have embeddings, approximate using content similarity
            max_similarity = 0.0
            for selected_chunk in selected:
                # Use Jaccard similarity as approximation
                similarity = _jaccard_similarity(
                    candidate.chunk.content,
                    selected_chunk.chunk.content
                )
                max_similarity = max(max_similarity, similarity)
            
            # Calculate MMR score
            mmr_score = lambda_mult * relevance - (1 - lambda_mult) * max_similarity
            
            if mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_idx = i
        
        if best_idx >= 0:
            selected.append(remaining.pop(best_idx))
        else:
            # No more valid candidates
            break
    
    return selected


def _jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity between two texts as word sets.
    
    This is a simple approximation for document similarity when
    embeddings are not available.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Jaccard similarity coefficient (0-1)
    """
    if not text1 or not text2:
        return 0.0
    
    # Convert to word sets (simple tokenization)
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0


def apply_mmr_with_embeddings(
    candidates: List[RetrievedChunk],
    query_vector: List[float],
    embeddings: List[List[float]],
    top_k: int,
    lambda_mult: float = 0.5
) -> List[RetrievedChunk]:
    """
    Apply MMR with actual embeddings for more accurate similarity calculation.
    
    This is the preferred method when embeddings are available.
    
    Args:
        candidates: List of retrieved chunks
        query_vector: Query embedding
        embeddings: Corresponding embeddings for each candidate
        top_k: Number of documents to select
        lambda_mult: Relevance vs diversity trade-off
        
    Returns:
        Re-ranked list of chunks
    """
    if not candidates or not embeddings or top_k <= 0:
        return []
    
    if len(candidates) != len(embeddings):
        raise ValueError("Number of candidates must match number of embeddings")
    
    if len(candidates) <= top_k:
        return candidates
    
    selected_indices = []
    remaining_indices = list(range(len(candidates)))
    
    # Convert to numpy arrays for efficient computation
    query_vec = np.array(query_vector)
    embed_matrix = np.array(embeddings)
    
    # First selection: highest similarity to query
    similarities = _cosine_similarity_batch(query_vec, embed_matrix)
    first_idx = np.argmax(similarities)
    selected_indices.append(remaining_indices.pop(first_idx))
    
    # Iteratively select remaining documents
    while len(selected_indices) < top_k and remaining_indices:
        best_idx = -1
        best_mmr_score = float('-inf')
        
        for i, cand_idx in enumerate(remaining_indices):
            # Relevance: similarity to query
            relevance = similarities[cand_idx]
            
            # Diversity: maximum similarity to selected documents
            selected_embeddings = embed_matrix[selected_indices]
            candidate_embedding = embed_matrix[cand_idx]
            
            diversities = _cosine_similarity_batch(candidate_embedding, selected_embeddings)
            max_diversity = np.max(diversities) if len(diversities) > 0 else 0.0
            
            # Calculate MMR score
            mmr_score = lambda_mult * relevance - (1 - lambda_mult) * max_diversity
            
            if mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_idx = i
        
        if best_idx >= 0:
            selected_indices.append(remaining_indices.pop(best_idx))
        else:
            break
    
    # Return selected candidates in MMR order
    return [candidates[i] for i in selected_indices]


def _cosine_similarity_batch(vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Calculate cosine similarity between a vector and matrix of vectors."""
    # Normalize vectors
    vec_norm = vec / (np.linalg.norm(vec) + 1e-8)
    matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8)
    
    # Calculate dot products
    return np.dot(matrix_norm, vec_norm)