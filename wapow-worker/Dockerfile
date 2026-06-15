# Stage 1: Build the Vue.js dashboard
FROM node:20-slim AS frontend-builder
WORKDIR /app/dashboard
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/ .
RUN npm run build

# Stage 2: Python runtime environment
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY scraper/ ./scraper/

# Copy compiled Vue frontend assets
COPY --from=frontend-builder /app/scraper/dist ./scraper/dist

# Expose port
EXPOSE 3003

# Run the application
CMD ["uvicorn", "scraper.main:app", "--host", "0.0.0.0", "--port", "3003"]
