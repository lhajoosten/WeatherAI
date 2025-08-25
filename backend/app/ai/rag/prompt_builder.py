"""Prompt building for RAG LLM generation."""

from typing import List, Dict, Any
import structlog

from .models import RetrievedChunk, PromptParts

logger = structlog.get_logger(__name__)


class PromptBuilder:
    """
    Builds prompts for LLM generation using retrieved context and templates.
    
    Enforces immutable prompt templates loaded from configuration.
    """
    
    def __init__(self, prompt_template_path: str = "app/prompts/qa_v1.txt"):
        """
        Initialize prompt builder.
        
        Args:
            prompt_template_path: Path to the prompt template file
        """
        self.prompt_template_path = prompt_template_path
        self.prompt_version = "qa_v1"
        
        # Load template on initialization
        self._template = self._load_template()
    
    def _load_template(self) -> Dict[str, str]:
        """
        Load prompt template from file.
        
        TODO: Implement actual file loading when prompt templates are created.
        For now, use hardcoded template.
        
        Returns:
            Dictionary with system_prompt and user_prompt templates
        """
        # Hardcoded template for now - should be loaded from file
        return {
            "system_prompt": """You are a helpful assistant that answers questions based on provided context. 

Guidelines:
- Use only the information provided in the context
- If the context doesn't contain enough information to answer the question, say so
- Provide clear, concise answers
- Include relevant citations when possible""",
            
            "user_prompt": """Context:
{context}

Question: {query}

Please answer the question based on the provided context."""
        }
    
    def build_prompt(
        self, 
        query: str, 
        retrieved_chunks: List[RetrievedChunk],
        include_citations: bool = True
    ) -> PromptParts:
        """
        Build a complete prompt from query and retrieved chunks.
        
        Args:
            query: User's question
            retrieved_chunks: List of relevant chunks from retrieval
            include_citations: Whether to include source citations in context
            
        Returns:
            PromptParts containing system prompt, user prompt, and context
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Build context from retrieved chunks
        context = self._build_context(retrieved_chunks, include_citations)
        
        # Fill templates
        system_prompt = self._template["system_prompt"]
        user_prompt = self._template["user_prompt"].format(
            context=context,
            query=query.strip()
        )
        
        logger.debug(
            "Built prompt",
            query_length=len(query),
            num_chunks=len(retrieved_chunks),
            context_length=len(context),
            prompt_version=self.prompt_version
        )
        
        return PromptParts(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context=context,
            prompt_version=self.prompt_version
        )
    
    def _build_context(
        self, 
        chunks: List[RetrievedChunk], 
        include_citations: bool = True
    ) -> str:
        """
        Build context string from retrieved chunks.
        
        Args:
            chunks: List of retrieved chunks
            include_citations: Whether to include source information
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant context available."
        
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            content = chunk.chunk.content.strip()
            
            if include_citations:
                # Include source ID and similarity score as citation
                source_info = f"[Source: {chunk.source_id or 'Unknown'}]"
                context_parts.append(f"{i}. {content} {source_info}")
            else:
                context_parts.append(f"{i}. {content}")
        
        return "\n\n".join(context_parts)
    
    def estimate_token_count(self, prompt_parts: PromptParts) -> int:
        """
        Estimate total token count for the prompt.
        
        Uses simple approximation - should be replaced with model-specific tokenizer.
        
        Args:
            prompt_parts: Complete prompt components
            
        Returns:
            Estimated token count
        """
        total_text = (
            prompt_parts.system_prompt + "\n\n" +
            prompt_parts.user_prompt
        )
        
        # Very rough approximation: ~1.3 tokens per word
        word_count = len(total_text.split())
        return int(word_count * 1.3)
    
    def get_template_info(self) -> Dict[str, Any]:
        """
        Get information about the current template.
        
        Returns:
            Template metadata
        """
        return {
            "version": self.prompt_version,
            "template_path": self.prompt_template_path,
            "system_prompt_length": len(self._template["system_prompt"]),
            "user_prompt_template": self._template["user_prompt"][:100] + "..." if len(self._template["user_prompt"]) > 100 else self._template["user_prompt"]
        }