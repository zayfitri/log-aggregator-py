# e. Docker (Wajib)
# VERSI FINAL: untuk Docker Compose

# 1. Base Image
FROM python:3.11-slim
LABEL maintainer="mahasiswa-uts@email.com"

# 2. Set Working Directory
WORKDIR /app

# --- TAMBAHAN UNTUK HEALTHCHECK ---
# Pindah ke root untuk install curl
USER root
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
# -----------------------------------

# 3. Buat non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
RUN chmod 775 /app

# 4. Ganti ke non-root user
USER appuser

# 5. Copy & Install Dependencies
COPY --chown=appuser:appuser requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy SELURUH Kode Aplikasi
# Kita copy semuanya (.), bukan hanya src/
COPY --chown=appuser:appuser . .

# 7. Buat folder data (untuk SQLite)
# PERBAIKAN: Tambahkan -p agar tidak error jika folder sudah ada
RUN mkdir -p /app/data

# 8. Expose Port
EXPOSE 8080

# 9. Perintah default (untuk service 'aggregator')
# PERBAIKAN: Gunakan 'python -m' agar 'uvicorn' ditemukan
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]