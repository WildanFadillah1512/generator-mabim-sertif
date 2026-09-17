# Gunakan image Python resmi yang ringan
FROM python:3.11-slim

# Set direktori kerja di dalam container
WORKDIR /app

# Salin file requirements terlebih dahulu
COPY requirements.txt .

# Install dependencies sistem yang diperlukan oleh Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser binaries (hanya chromium untuk menghemat tempat)
RUN playwright install chromium
RUN playwright install-deps chromium

# Salin seluruh file proyek ke dalam container
COPY . .

# Expose port yang digunakan Flask/Gunicorn
EXPOSE 5000

# Perintah untuk menjalankan aplikasi menggunakan Gunicorn untuk production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
