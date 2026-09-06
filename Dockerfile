FROM python:3.11-slim

WORKDIR /app

# Install build essential dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose ports: 8000 for FastAPI backend, 8501 for Streamlit dashboard
EXPOSE 8000 8501

ENV PORT=8501
ENV API_BASE_URL=http://127.0.0.1:8000
ENV PYTHONPATH=/app

# Default command runs both FastAPI backend and Streamlit visual UI
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 & streamlit run dashboard/streamlit_app.py --server.port $PORT --server.address 0.0.0.0"]
