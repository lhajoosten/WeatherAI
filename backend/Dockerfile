# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# Install basic system dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      bash \
      curl \
      ca-certificates \
      build-essential \
      libpq-dev \
      locales \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy and install Python dependencies with trusted hosts for CI environment
COPY pyproject.toml ./
RUN pip install -e .[dev]

# Copy application code
COPY . .

# Copy and set permissions for entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh \
    && chmod +x /usr/local/bin/entrypoint.sh
    
# Create non-root user
RUN useradd --create-home --shell /bin/bash weatherai
RUN chown -R weatherai:weatherai /app
USER weatherai

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]