# Base — Python 3.11 slim
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependencies first — Docker caches this layer
# If your code changes but requirements.txt doesn't,
# Docker skips reinstalling packages. Faster rebuilds.
COPY api/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser

# Now copy the rest of your code
COPY api/ ./api/

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Cloud Run sets PORT automatically — your app must listen on it
ENV PORT=8080

# Start the server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
