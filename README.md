<<<<<<< HEAD
UTS Sistem Terdistribusi - Pub-Sub Log Aggregator

Proyek ini adalah implementasi layanan log aggregator dengan idempotent consumer dan deduplikasi, sesuai spesifikasi UTS.

Fitur Utama

API Server (FastAPI): Menerima event tunggal atau batch via POST /publish.

Async Consumer: Memproses event secara asinkron menggunakan asyncio.Queue.

Idempotency & Deduplication: Menggunakan SQLite dengan PRIMARY KEY (topic, event_id) untuk mencegah pemrosesan duplikat.

Persistensi: Deduplication store (SQLite) bersifat persisten dan tahan restart (disimpan di file data/dedup_store.db).

Observability: Menyediakan endpoint GET /stats dan GET /events untuk memantau sistem.

Containerized: Sepenuhnya berjalan di dalam Docker.

Bonus: Termasuk docker-compose.yml untuk orkestrasi aggregator dan publisher.

Struktur Proyek

.
├── data/                  # Folder untuk database SQLite (dibuat otomatis)
├── src/
│   ├── __init__.py
│   ├── main.py            # Aplikasi FastAPI, API endpoints, consumer task
│   ├── models.py          # Model Pydantic (Skema Event)
│   └── database.py        # Logika interaksi SQLite (deduplikasi)
├── tests/
│   └── test_main.py       # Unit tests (pytest)
├── tools/
│   └── stress_test.py     # Script stress test (5000+ events)
├── Dockerfile             # Wajib: Resep untuk build image
├── docker-compose.yml     # Opsional (Bonus): Menjalankan aggregator + publisher
├── requirements.txt       # Dependensi Python
├── report.md              # Laporan Analisis Teori (T1-T8)
└── README.md              # File ini


Cara Menjalankan

Ada dua cara untuk menjalankan proyek ini:

Opsi 1: Menggunakan Docker Compose (Direkomendasikan, untuk Bonus)

Cara ini akan otomatis menjalankan service aggregator DAN service publisher (stress_test.py) yang akan mengirim 5.000 event.

Pastikan Docker dan Docker Compose terinstal.

Buka terminal di root folder proyek ini.

Jalankan build dan run:

docker-compose up --build


Anda akan melihat log dari aggregator-service (server siap) dan publisher-client (mengirim event).

Setelah publisher selesai, server akan tetap berjalan.

Opsi 2: Menggunakan Docker Saja (Manual)

Cara ini hanya menjalankan service aggregator. Anda harus menjalankan publisher (stress test) secara manual dari host Anda.

1. Build Image
Sesuai instruksi:

docker build -t uts-aggregator .


2. Run Container
Sesuai instruksi. Perintah -v $(pwd)/data:/app/data penting untuk menyimpan database di host Anda (agar persisten).

# Untuk Linux/macOS
docker run -d -p 8080:8080 -v $(pwd)/data:/app/data --name aggregator uts-aggregator

# Untuk Windows (Command Prompt)
docker run -d -p 8080:8080 -v "%cd%/data":/app/data --name aggregator uts-aggregator


Server Anda sekarang berjalan di http://127.0.0.1:8080.

3. Jalankan Stress Test (Manual)
Buka terminal kedua di host Anda dan jalankan script stress_test.py:

pip install -r requirements.txt
python tools/stress_test.py


Endpoint API (Setelah Server Berjalan)

Dokumentasi Interaktif: http://127.0.0.1:8080/docs

Publish Event: POST /publish

Lihat Statistik: http://127.0.0.1:8080/stats

Lihat Event Unik: http://127.0.0.1:8080/events

Filter Event: http://127.0.0.1:8080/events?topic=auth.prod

Menjalankan Unit Tests

Pastikan Anda berada di root proyek.

Instal dependencies (termasuk pytest).

pip install -r requirements.txt


Jalankan pytest:

pytest


Link Video Demo

(Sesuai instruksi, unggah video demo 5-8 menit ke YouTube dan letakkan link-nya di sini)

[LINK_VIDEO_YOUTUBE_ANDA_DI_SINI]
=======
# log-aggregator-py
>>>>>>> 86edee2daa01813b783ca07b8b18fbfdfa354c97
