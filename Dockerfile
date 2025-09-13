# Enhanced Premier League MCP Server with Supabase Caching
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose MCP server port
EXPOSE 5000

# Environment variables
ENV PYTHONPATH=/app/src
ENV ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.database.connection import test_db_connection; exit(0 if test_db_connection() else 1)" || exit 1

# Run the enhanced MCP server
CMD ["python", "soccer_server.py"]

