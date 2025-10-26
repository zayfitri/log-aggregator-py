# UTS Sistem Terdistribusi: Pub-Sub Log Aggregator
Proyek ini adalah implementasi layanan log aggregator sederhana menggunakan arsitektur publish-subscribe internal, dibangun sebagai tugas Ujian Tengah Semester (UTS) mata kuliah Sistem Paralel dan Terdistribusi.

Fitur utama meliputi penerimaan event log, idempotent consumer untuk mencegah pemrosesan ganda, deduplication menggunakan SQLite, dan persistensi data saat container restart. Seluruh sistem berjalan di Docker dan Docker Compose.

Nama: Isnaini Zayyana Fitri
NIM: 11221072

# Teknologi yang Digunakan:
Python 3.11
FastAPI
asyncio (asyncio.Queue)
SQLite3
Docker & Docker Compose
Pytest, httpx, pytest-asyncio, anyio


# Cara Menjalankan
Prasyarat:
Docker Engine dan Docker Compose terinstall.
Terminal (CMD, PowerShell, bash, dll).

Langkah-langkah:
1. Clone Repository (jika belum):
git clone [https://github.com/zayfitri/log-aggregator-py.git](https://github.com/zayfitri/log-aggregator-py.git)
cd log-aggregator-py

2. Jalankan Build & Stress Test (Publisher + Aggregator):
Perintah ini akan membangun image Docker dan menalankan  kedua service. Publisher akan mengirim 5000 event (dengan ~20% duplikasi) ke Aggregator.
docker-compose up --build
- Amati log untuk melihat proses penerimaan, deduplikasi (UNIK vs DUPLIKAT).
- Tunggu hingga publisher selesai (log publisher-client exited with code 0).
- Sebelum mematikan, Anda bisa cek http://localhost:8080/stats di browser untuk melihat statistik awal (received ~5000).
- Tekan Ctrl + C untuk menghentikan semua service.

3. Jalankan Aggregator Saja (Untuk Cek Persistensi):
Perintah ini hanya akan menjalankan service aggregator.
docker-compose up aggregator
- Server akan membaca ulang data dari data/dedup_store.db.
- Buka browser Anda untuk memeriksa hasil akhir:
    - http://localhost:8080/stats (Akan menunjukkan unique_processed (total) ~4000).
    - http://localhost:8080/events?topic=auth.prod (Akan menampilkan daftar event unik).
    - http://localhost:8080/events?topic=payment.dev
    - http://localhost:8080/events?topic=logs.staging
- Tekan Ctrl + C untuk menghentikan server jika sudah selesai.

4. Jalankan Unit Tests:
Perintah ini akan menjalankan 6 unit test menggunakan pytest di dalam container baru.
docker-compose run --build --rm aggregator python -m pytest
- Pastikan hasilnya menunjukkan ======= 6 passed =======.

# Endpoint API
- POST /publish: Menerima satu atau batch event JSON.
    - Body (Single): { "topic": "...", "event_id": "...", ... }
    - Body (Batch): [{...}, {...}, ...]
    - Respons Sukses: 202 Accepted
- GET /stats: Mengembalikan statistik pemrosesan event.
- GET /events: Mengembalikan daftar semua event unik yang telah diproses.
- GET /events?topic={nama_topic}: Mengembalikan daftar event unik yang telah diproses untuk topic tertentu.
- GET /: Endpoint root untuk health check.

# Video Demo
Demonstrasi lengkap sistem ini dapat dilihat di YouTube:
[https://youtu.be/Emw6gazfT4k?si=-aMhJfsy-7xADMdY]

# Laporan Proyek
Penjelasan detail mengenai desain, analisis teori, analisis performa, dan keterkaitan dengan buku utama dapat ditemukan dalam file **report.pdf**