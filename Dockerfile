# Gunakan image Python versi bookworm (lebih stabil dari slim untuk instalasi C-libraries)
FROM python:3.11-bookworm

# Set direktori kerja di dalam container
WORKDIR /app

# Salin file requirements terlebih dahulu
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright beserta dependency sistem bawaannya secara otomatis
RUN playwright install chromium
RUN playwright install-deps chromium

# Salin seluruh file proyek ke dalam container
COPY . .

# Expose port yang digunakan Flask/Gunicorn
EXPOSE 5000

# Perintah untuk menjalankan aplikasi menggunakan Gunicorn untuk production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
