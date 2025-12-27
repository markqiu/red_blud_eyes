# Use Python 3.11 runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for faster package installation
RUN pip install --no-cache-dir uv

# Copy requirements and install dependencies using uv
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check using curl (lighter than requests)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=5)"

# Run the application
CMD ["python", "src/web_server.py"]
