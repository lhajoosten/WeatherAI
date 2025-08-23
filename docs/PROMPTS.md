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