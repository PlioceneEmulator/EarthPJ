FROM python:3.9

# Install system dependencies for scientific computing
RUN apt-get update && apt-get install -y \
    build-essential \
    libproj-dev \
    proj-data \
    proj-bin \
    libgeos-dev \
    libgeos++-dev \
    libgeos-c1v5 \
    libgdal-dev \
    gdal-bin \
    python3-gdal \
    libhdf5-dev \
    libnetcdf-dev \
    libopenblas-dev \
    gfortran \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip wheel setuptools
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Create necessary directories
RUN mkdir -p website/static website/templates

# Set environment variables
ENV FLASK_APP=webapp.py
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--timeout", "120", "webapp:app"]