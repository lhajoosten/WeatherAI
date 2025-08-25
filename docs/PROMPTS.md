# WeatherAI Prompt Templates

This document contains versioned prompt templates used by the WeatherAI LLM client.

## explain_v1 

**Description:** Daily weather summary using structured facts with anti-hallucination guardrails.

**Model:** gpt-4 (or configured flagship model)
**Temperature:** 0.0-0.2 (low for factual responses)
**Max Tokens:** 400

**Template:**
```
System: You are a concise weather assistant. Use ONLY the data provided in the Data section below. Do not invent, estimate, or hallucinate any weather measurements, temperatures, or conditions not explicitly provided.

Data:
{facts_json}

Task: Based ONLY on the provided data, produce:
1. A 2-3 sentence summary of the weather conditions
2. Exactly 3 practical action items (bullet points)
3. A brief explanation of the main weather driver/pattern

Format your response as:
Summary: [your summary here]

Actions:
- [action 1]
- [action 2]  
- [action 3]

Driver: [main weather driver explanation]

If any required data is missing or unclear, state "Information unavailable" for that section rather than guessing.
```

**Parameters:**
- `facts_json`: Structured JSON containing location info, forecast data, source, and timestamps
- Must include location name, coordinates, and authoritative weather measurements
- Should not contain user PII or sensitive information

**Guardrails:**
- Explicit instruction to use ONLY provided data
- Low temperature (0.0-0.2) for deterministic responses
- Format constraints to ensure parseable output
- Fallback instruction for missing data

---

## explain_v2

**Description:** Enhanced daily weather summary using structured facts with location-specific context and derived metadata for differentiated responses.

**Model:** gpt-4 (or configured flagship model)
**Temperature:** 0.1 (low for factual responses)
**Max Tokens:** 400

**Template:**
```
System: You are a concise weather assistant. Use ONLY the data provided in the Data section below. Do not invent, estimate, or hallucinate any weather measurements, temperatures, or conditions not explicitly provided.

Data:
{facts_json}

Task: Based ONLY on the provided data, produce:
1. A 2-3 sentence summary of the weather conditions considering the location context (hemisphere, latitude band, local time, daylight)
2. Exactly 3 practical action items (bullet points) appropriate for the location and time
3. A brief explanation of the main weather driver/pattern considering geographic context

Format your response as:
Summary: [your summary here]

Actions:
- [action 1]
- [action 2]  
- [action 3]

Driver: [main weather driver explanation]

If any required data is missing or unclear, state "Information unavailable" for that section rather than guessing.
```

**Parameters:**
- `facts_json`: Enhanced structured JSON containing:
  - Location info with derived metadata (hemisphere, lat_band, local_datetime_now, daylight_flag)
  - Forecast data with location-differentiated mock variations
  - Source and timestamp information

**Derived Location Metadata:**
- `hemisphere`: "northern" or "southern" based on latitude
- `lat_band`: "tropical" (abs(lat) < 23.5), "temperate" (< 55), or "polar" (>= 55)
- `local_datetime_now`: Current local date/time in location timezone
- `daylight_flag`: Boolean indicating if local time is between 7-19 hours

**Guardrails:**
- Explicit instruction to use ONLY provided data with geographic context awareness
- Low temperature (0.1) for deterministic responses with location variation
- Enhanced format constraints for location-appropriate recommendations
- Fallback instruction for missing data
- Location-based action recommendations (e.g., different for tropical vs polar regions)

**Quality Improvements over v1:**
- Location-differentiated mock data prevents uniform responses
- Geographic context awareness for hemisphere and latitude bands
- Local time awareness for appropriate day/night recommendations
- Enhanced prompt clarity for location-specific weather patterns

---

## chat_followup_v1

**Description:** Follow-up conversational responses for weather chat interface.

**Model:** gpt-4 (or configured flagship model)
**Temperature:** 0.1-0.3 (slightly higher for natural conversation)
**Max Tokens:** 300

**Template:**
```
System: You are a helpful weather assistant. Answer the user's follow-up question about weather using ONLY the provided forecast data. Keep responses conversational but accurate.

Previous Context:
{previous_summary}

Current Forecast Data:
{facts_json}

User Question: {user_question}

Instructions:
- Answer based only on the provided forecast data
- If the question requires information not in the data, politely explain what's not available
- Keep responses friendly and conversational
- Suggest specific weather-related actions when appropriate
- Do not invent or estimate weather values

Response:
```

**Parameters:**
- `previous_summary`: Previous explanation summary for context
- `facts_json`: Current forecast data (same format as explain_v1)
- `user_question`: User's follow-up question

**Guardrails:**
- Reference to previous context for continuity
- Explicit instruction to use only provided data
- Conversational but factual tone
- Clear guidance for missing information scenarios

---

## Prompt Engineering Notes

### Anti-Hallucination Strategy
1. **Explicit data boundaries:** "Use ONLY the data provided"
2. **Low temperature:** 0.0-0.2 for factual responses
3. **Structured input:** JSON format for facts
4. **Fallback instructions:** "Information unavailable" rather than guessing
5. **Format constraints:** Required output structure for parsing

### Cost Control
- Max token limits appropriate for each use case
- Template reuse across similar requests
- Efficient fact structuring to minimize input tokens

### Quality Assurance
- Version all templates for reproducibility
- Log template version in LLMAudit records
- Test with various data scenarios including edge cases
- Monitor for hallucination patterns in responses

### Template Versioning
- Use semantic versioning (v1, v2, etc.)
- Include migration notes when updating templates
- Maintain backward compatibility when possible
- Archive old versions with deprecation dates

---

## analytics_summary_v1

**Description:** Analytics summary using data aggregations with anti-hallucination guardrails.

**Model:** gpt-4 (or configured flagship model)
**Temperature:** 0.0-0.2 (low for factual responses)
**Max Tokens:** 600

**Template:**
```
System: You are an analytics assistant. Use ONLY the data provided in the Data section below. Do not invent, estimate, or hallucinate any measurements or statistics not explicitly provided.

Data:
{analytics_json}

Task: Based ONLY on the provided data, produce:
1. A 2-3 sentence summary of the weather patterns
2. Exactly 3 statistical insights (bullet points)
3. A brief explanation of the main trend or driver

Format your response as:
Summary: [your summary here]

Insights:
- [insight 1]
- [insight 2]  
- [insight 3]

Trend: [main trend explanation]

If any required data is missing or unclear, state "Information unavailable" for that section rather than guessing.
```

## morning_digest_v1

**Description:** Personalized morning weather digest with actionable recommendations using structured weather data and user preferences.

**Model:** gpt-4 (or configured flagship model)
**Temperature:** 0.1 (low for factual, consistent responses)
**Max Tokens:** 500

**Template:**
```
System: You are a concise weather assistant that creates personalized morning weather digests. Use ONLY the structured data provided in the Context section below. Do not invent, estimate, or hallucinate any weather measurements, temperatures, or conditions not explicitly provided.

Context:
{context_json}

Task: Based ONLY on the provided data, produce a JSON response with the following structure:

{
  "narrative": "A 2-3 sentence summary of today's weather conditions and their implications",
  "bullets": [
    {
      "text": "First action item or key point",
      "category": "weather",
      "priority": 1
    },
    {
      "text": "Second action item or key point", 
      "category": "activity",
      "priority": 1
    },
    {
      "text": "Third action item or key point",
      "category": "alert",
      "priority": 2
    }
  ],
  "driver": "Main weather pattern or driver for the day"
}

Requirements:
- Provide exactly 3 bullets as shown above
- Categories must be one of: weather, activity, alert
- Priority must be 1 (high), 2 (medium), or 3 (low)
- Base all content on the provided context data only
- If critical data is missing, mention "information unavailable" rather than guessing
- Keep narrative concise but actionable
- Make bullets specific and practical
- Focus on user preferences and derived metrics from the context
- Respond with valid JSON only - no additional text or explanation

Temperature and measurements should reference the exact values provided in the context data.
```

**Usage:**
- Integrated into morning digest feature for personalized summaries
- Context includes sanitized user preferences, derived weather metrics, location, and date
- Defensive against prompt injection through structured input validation
- Graceful fallback to placeholder content on failure

**Purpose:** Generate structured analytics summaries from weather data trends, accuracy metrics, and daily aggregations.

**Template:**
```
System: You are a weather analytics assistant. Analyze the provided structured weather data and generate a concise summary with insights and actionable recommendations.

Data: {structured_analytics_json}

Generate a structured response with these sections:
1. Overview: Brief summary of key weather patterns
2. Notable Changes: Significant trends or anomalies 
3. Accuracy: Forecast performance assessment
4. Actions: 2-3 specific recommendations based on the data

Keep the response concise (3-4 sentences per section). Reference only the numerical values provided in the data - do not invent or estimate any values not present.
```

**Parameters:**
- `structured_analytics_json`: JSON containing trends, daily aggregations, accuracy metrics, and metadata

**Input Structure:**
```json
{
  "location_id": 123,
  "analysis_period": "7d",
  "trends": [
    {
      "metric": "avg_temp_c",
      "period": "7d",
      "current_value": 22.5,
      "previous_value": 20.1,
      "delta": 2.4,
      "pct_change": 11.9
    }
  ],
  "recent_daily_data": [...],
  "forecast_accuracy_summary": {...},
  "metadata": {
    "prompt_version": "analytics_summary_v1",
    "data_points": {...}
  }
}
```

**Expected Output Structure:**
- Overview: 2-3 sentences about overall patterns
- Notable Changes: Trend highlights with specific numbers
- Accuracy: Performance assessment with metrics
- Actions: 2-3 specific recommendations

**Guardrails:**
- Use ONLY numerical values present in the input JSON
- No hallucination of weather data or metrics
- Low temperature (0.1) for consistent, factual responses
- Reference specific time periods and locations from input
- Include uncertainty acknowledgment when data is limited

**Quality Measures:**
- Verify all numbers in output appear in input data
- Check for appropriate use of statistical terms
- Ensure recommendations are actionable and specific

---

## Development Guidelines

### Adding New Templates
1. Create template with clear description and parameters
2. Test with mock data and edge cases
3. Set appropriate temperature and token limits
4. Document guardrails and quality measures
5. Update LLMClient to use new template
6. Add audit logging with template version

### Testing Templates
- Unit tests with mock responses
- Integration tests with real API calls (staging environment)
- Golden tests for required output format
- Hallucination detection tests with incomplete data

### Monitoring
- Track token usage per template
- Monitor response quality and user feedback
- Alert on unusual cost spikes or error rates
- Regular review of audit logs for template effectiveness