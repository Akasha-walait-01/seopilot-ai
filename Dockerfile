FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser
RUN playwright install --with-deps chromium

# Copy project
COPY . .

# Hugging Face Space port
EXPOSE 8080

# Start backend + frontend
CMD ["bash", "start.sh"]