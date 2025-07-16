# Multi-stage build for optimized container size
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/mcpuser/.local

# Copy application code
COPY memento_mcp_server.py .
COPY requirements.txt .

# Create storage directory with proper permissions
RUN mkdir -p /app/memento_storage && \
    chown -R mcpuser:mcpuser /app

# Set environment variables
ENV PYTHONPATH=/home/mcpuser/.local/lib/python3.10/site-packages
ENV PATH=/home/mcpuser/.local/bin:$PATH
ENV MCP_SSE_HOST=0.0.0.0
ENV MCP_SSE_PORT=8000

# Expose port
EXPOSE 8000

# Install curl for health check
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER mcpuser

# Run the application
CMD ["python", "memento_mcp_server.py"]
