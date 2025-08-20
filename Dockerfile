# Multi-platform deployment Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE $PORT

# Run the application
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true