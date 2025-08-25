# Configuration Guide

WeatherAI uses environment variables for configuration with sensible defaults. This document describes all available configuration options and their usage.

## Configuration Loading

The application uses Pydantic Settings for configuration management with the following precedence:

1. **Environment variables** (highest priority)
2. **Default values** (lowest priority)

Use the `get_settings()` function to access configuration:

```python
from app.core.config import get_settings

settings = get_settings()  # Returns cached singleton instance
```

## Configuration Sections

### Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `"dev"` | Environment name (`dev`, `staging`, `prod`) |
| `LOG_LEVEL` | `"INFO"` | Logging level |
| `ENABLE_METRICS` | `true` | Enable metrics collection |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_SERVER` | `"localhost"` | MSSQL server hostname |
| `DB_PORT` | `1433` | MSSQL server port |
| `DB_NAME` | `"WeatherAI"` | Database name |
| `DB_USER` | `"sa"` | Database username |
| `DB_PASSWORD` | `"YourStrong@Passw0rd"` | Database password |

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `"redis://redis:6379"` | Redis connection URL |

### Azure OpenAI Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_OPENAI_ENDPOINT` | `None` | Azure OpenAI service endpoint |
| `AZURE_OPENAI_API_KEY` | `None` | Azure OpenAI API key |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | `None` | Embedding model deployment name |
| `AZURE_OPENAI_EMBEDDING_DIM` | `1536` | Embedding vector dimension |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | `None` | Chat model deployment name |

### RAG Pipeline Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `RAG_CHUNK_SIZE` | `512` | Target tokens per text chunk |
| `RAG_CHUNK_OVERLAP` | `50` | Token overlap between chunks |
| `RAG_SIMILARITY_THRESHOLD` | `0.75` | Minimum similarity for retrieval |
| `RAG_TOP_K` | `6` | Maximum chunks to retrieve |
| `RAG_MMR_LAMBDA` | `0.5` | MMR relevance vs diversity trade-off |
| `RAG_ANSWER_CACHE_TTL_SECONDS` | `21600` | Answer cache TTL (6 hours) |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | General API rate limit |
| `LLM_RATE_LIMIT_REQUESTS_PER_MINUTE` | `10` | LLM-specific rate limit |

## Environment Files

Create a `.env` file in the backend directory for local development:

```bash
# .env
ENV=dev
LOG_LEVEL=DEBUG

# Azure OpenAI (required for RAG)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4

# Database (adjust for your setup)
DB_SERVER=localhost
DB_PASSWORD=YourActualPassword

# Redis (adjust for your setup)
REDIS_URL=redis://localhost:6379
```

## Validation Rules

The configuration system enforces the following validation rules:

- `AZURE_OPENAI_EMBEDDING_DIM` must be positive
- `RAG_CHUNK_OVERLAP` must be less than `RAG_CHUNK_SIZE`
- Invalid configurations will raise `ValueError` on startup

## Secret Management

The system includes a placeholder for Azure Key Vault integration:

```python
def load_secrets_from_key_vault(settings: AppSettings) -> None:
    """Load secrets from Azure Key Vault (placeholder)."""
    # TODO: Implement actual Key Vault integration
    pass
```

For production deployments, consider:

1. Azure Key Vault for secret storage
2. Managed identities for authentication
3. Environment-specific configuration files
4. Container orchestration secrets management

## Example Usage

```python
from app.core.config import get_settings

# Get configuration
settings = get_settings()

# Access values
chunk_size = settings.rag_chunk_size
api_endpoint = settings.azure_openai_endpoint

# Database URL is dynamically generated
db_url = settings.database_url  # Property method
```

## Development vs Production

### Development
- Use `.env` file for local configuration
- Enable debug logging (`LOG_LEVEL=DEBUG`)
- Lower security requirements

### Production
- Use environment variables or secret management
- Set `ENV=prod`
- Enable metrics and monitoring
- Use secure database credentials
- Configure proper CORS origins

## Troubleshooting

### Common Issues

1. **Configuration not loading**: Ensure environment variables are set correctly
2. **Validation errors**: Check that chunk overlap < chunk size and embedding dimension > 0
3. **Database connection fails**: Verify database credentials and network connectivity
4. **Redis connection fails**: Check Redis URL and service availability
5. **Azure OpenAI errors**: Validate endpoint, API key, and deployment names

### Debug Configuration

```python
from app.core.config import get_settings

settings = get_settings()
print(f"Current environment: {settings.env}")
print(f"Database URL: {settings.database_url}")
print(f"RAG settings: chunk_size={settings.rag_chunk_size}, overlap={settings.rag_chunk_overlap}")
```