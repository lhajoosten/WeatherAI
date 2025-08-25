"""Prompt builder for morning digest LLM requests.

This module constructs structured JSON context for the morning digest LLM prompt,
ensuring all user input is sanitized and no free-form text is passed directly.
"""

import json
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Prompt version constant - immutable
MORNING_DIGEST_PROMPT_VERSION = "morning_digest_v1"

# Maximum lengths for text fields to prevent token overflow
MAX_TEXT_LENGTHS = {
    "location_name": 100,
    "activity_conditions": 200,
    "preference_values": 50,
    "activity_type": 30
}

# Whitelisted user preference keys to prevent injection
ALLOWED_PREFERENCE_KEYS = {
    'outdoor_activities', 'temperature_tolerance', 'rain_tolerance', 
    'units_system', 'activity_level', 'time_preference'
}


class DigestPromptBuilder:
    """Builds structured prompts for morning digest LLM generation."""
    
    def __init__(self):
        """Initialize the prompt builder."""
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """Load the prompt template from file."""
        prompt_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "prompts", "morning_digest_v1.txt"
        )
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.error(f"Prompt template not found: {prompt_path}")
            raise FileNotFoundError(f"Morning digest prompt template not found: {prompt_path}")
    
    def build_context(
        self,
        date: str,
        location_name: str,
        user_preferences: Dict[str, Any],
        derived_metrics: Dict[str, Any],
        style_examples: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Build structured JSON context for the LLM prompt.
        
        Args:
            date: Target date (YYYY-MM-DD)
            location_name: Location name for context
            user_preferences: User preferences dictionary
            derived_metrics: Derived weather metrics from forecast
            style_examples: Optional style examples for consistency
            
        Returns:
            Structured context dictionary for JSON serialization
        """
        logger.debug(
            "Building morning digest context",
            date=date,
            location=location_name[:50],  # Truncate for logging
            preferences_keys=list(user_preferences.keys())
        )
        
        # Sanitize inputs
        sanitized_location = self._sanitize_text(location_name, "location_name")
        sanitized_preferences = self._sanitize_preferences(user_preferences)
        sanitized_derived = self._sanitize_derived_metrics(derived_metrics)
        
        # Build constraints section
        constraints = {
            "max_narrative_sentences": 3,
            "required_bullets": 3,
            "bullet_categories": ["weather", "activity", "alert"],
            "priority_levels": [1, 2, 3],
            "temperature_unit": sanitized_preferences.get("units_system", "metric")
        }
        
        # Construct main context
        context = {
            "date": date,
            "location": sanitized_location,
            "user_preferences": sanitized_preferences,
            "derived": sanitized_derived,
            "constraints": constraints
        }
        
        # Add style examples if provided
        if style_examples:
            context["style_examples"] = style_examples
        
        logger.debug("Context built successfully", context_keys=list(context.keys()))
        return context
    
    def build_prompt(
        self,
        date: str,
        location_name: str,
        user_preferences: Dict[str, Any],
        derived_metrics: Dict[str, Any],
        style_examples: Dict[str, Any] = None
    ) -> str:
        """Build the complete prompt with context JSON embedded.
        
        Args:
            date: Target date (YYYY-MM-DD)
            location_name: Location name for context
            user_preferences: User preferences dictionary
            derived_metrics: Derived weather metrics from forecast
            style_examples: Optional style examples for consistency
            
        Returns:
            Complete prompt string ready for LLM
        """
        context = self.build_context(
            date=date,
            location_name=location_name,
            user_preferences=user_preferences,
            derived_metrics=derived_metrics,
            style_examples=style_examples
        )
        
        # Serialize context to JSON
        context_json = json.dumps(context, indent=2, default=str)
        
        # Embed in template
        prompt = self.prompt_template.replace("{context_json}", context_json)
        
        # Estimate token count for defensive limits
        estimated_tokens = len(prompt.split()) * 1.3
        logger.debug(
            "Prompt built",
            estimated_tokens=int(estimated_tokens),
            context_size=len(context_json)
        )
        
        return prompt
    
    def _sanitize_text(self, text: str, field_name: str) -> str:
        """Sanitize text input for safe inclusion in context.
        
        Args:
            text: Input text to sanitize
            field_name: Field name for length limits
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return str(text)
        
        # Remove potential injection characters and normalize whitespace
        sanitized = text.replace('\n', ' ').replace('\r', ' ').replace('"', "'")
        sanitized = ' '.join(sanitized.split())  # Normalize whitespace
        
        # Apply length limits
        max_length = MAX_TEXT_LENGTHS.get(field_name, 100)
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].strip()
            logger.debug(f"Truncated {field_name}", original_length=len(text), final_length=len(sanitized))
        
        return sanitized
    
    def _sanitize_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize user preferences with whitelist and length limits.
        
        Args:
            preferences: Raw user preferences
            
        Returns:
            Sanitized preferences dictionary
        """
        sanitized = {}
        
        for key, value in preferences.items():
            # Only include whitelisted keys
            if key in ALLOWED_PREFERENCE_KEYS:
                if isinstance(value, str):
                    sanitized[key] = self._sanitize_text(value, "preference_values")
                elif isinstance(value, (bool, int, float)):
                    sanitized[key] = value
                else:
                    # Convert complex types to string and sanitize
                    sanitized[key] = self._sanitize_text(str(value), "preference_values")
        
        logger.debug(
            "Preferences sanitized", 
            original_keys=len(preferences), 
            sanitized_keys=len(sanitized)
        )
        return sanitized
    
    def _sanitize_derived_metrics(self, derived: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize derived metrics for safe context inclusion.
        
        Args:
            derived: Raw derived metrics
            
        Returns:
            Sanitized derived metrics
        """
        sanitized = {}
        
        # Copy safe numeric fields directly
        numeric_fields = {
            'temp_min_c', 'temp_max_c', 'comfort_score'
        }
        
        for field in numeric_fields:
            if field in derived:
                sanitized[field] = derived[field]
        
        # Handle time windows with validation
        for window_field in ['peak_rain_window', 'lowest_wind_window']:
            if window_field in derived and derived[window_field]:
                window = derived[window_field]
                if hasattr(window, 'start_hour') and hasattr(window, 'end_hour'):
                    sanitized[window_field] = {
                        'start_hour': window.start_hour,
                        'end_hour': window.end_hour,
                        'duration_hours': getattr(window, 'duration_hours', window.end_hour - window.start_hour)
                    }
        
        # Handle activity blocks with text sanitization
        if 'activity_blocks' in derived:
            sanitized_blocks = []
            for block in derived['activity_blocks']:
                if hasattr(block, 'activity_type') and hasattr(block, 'conditions'):
                    sanitized_block = {
                        'activity_type': self._sanitize_text(block.activity_type, "activity_type"),
                        'conditions': self._sanitize_text(block.conditions, "activity_conditions"),
                        'suitability_score': getattr(block, 'suitability_score', 0.0)
                    }
                    
                    # Add time window if present
                    if hasattr(block, 'time_window'):
                        sanitized_block['time_window'] = {
                            'start_hour': block.time_window.start_hour,
                            'end_hour': block.time_window.end_hour
                        }
                    
                    sanitized_blocks.append(sanitized_block)
            
            sanitized['activity_blocks'] = sanitized_blocks
        
        logger.debug("Derived metrics sanitized", fields=list(sanitized.keys()))
        return sanitized


# Factory function for easy instantiation
def create_digest_prompt_builder() -> DigestPromptBuilder:
    """Create a new digest prompt builder instance."""
    return DigestPromptBuilder()