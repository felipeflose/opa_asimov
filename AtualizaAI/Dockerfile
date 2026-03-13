# Optimized Dockerfile for Flose AI Platform

FROM python:3.11

WORKDIR /app

# The full python:3.11 image already has build-essential
# We only need Git if we are installing from git repos
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8080

# Environment variables for GCP
ENV PORT=8080
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

CMD ["streamlit", "run", "src/dashboard/Home.py"]
