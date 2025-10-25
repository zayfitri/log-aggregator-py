# src/database.py
# VERSI FINAL (FIXED 2) - Tambah fungsi get_all_processed_events

import sqlite3
import os
import logging
from datetime import datetime
import json # Untuk deserialize payload

# Import model Event (relatif dari folder src)
from .models import Event

# Path database di dalam folder 'data'
DB_FOLDER = "data"
DB_NAME = os.path.join(DB_FOLDER, "dedup_store.db")

def setup_database():
    """Membuat folder data dan tabel SQLite jika belum ada."""
    try:
        os.makedirs(DB_FOLDER, exist_ok=True) 

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # Modifikasi tabel: Tambahkan kolom payload (JSON text)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_events (
                topic TEXT NOT NULL,
                event_id TEXT NOT NULL,
                timestamp TEXT, 
                source TEXT,
                payload TEXT, -- Simpan payload sebagai JSON string
                processed_at TEXT DEFAULT CURRENT_TIMESTAMP, 
                PRIMARY KEY (topic, event_id)
            )
        ''')
        # Cek apakah kolom payload sudah ada (untuk migrasi jika DB sudah ada)
        cursor.execute("PRAGMA table_info(processed_events)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'payload' not in columns:
            logging.info("Menambahkan kolom 'payload' ke database...")
            cursor.execute("ALTER TABLE processed_events ADD COLUMN payload TEXT")

        conn.commit()
        conn.close()
        logging.info(f"Database '{DB_NAME}' berhasil disiapkan.")
    except Exception as e:
        logging.error(f"Gagal menyiapkan database: {e}", exc_info=True)
        raise 

def check_and_insert_event(event: Event) -> bool:
    """
    Mencoba memasukkan event ke DB. 
    Mengembalikan True jika unik (berhasil insert), False jika duplikat.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Serialize payload ke JSON string
        payload_str = json.dumps(event.payload)

        # Coba INSERT. Jika PRIMARY KEY sudah ada, akan gagal.
        cursor.execute('''
            INSERT INTO processed_events (topic, event_id, timestamp, source, payload)
            VALUES (?, ?, ?, ?, ?)
        ''', (event.topic, event.event_id, event.timestamp.isoformat(), event.source, payload_str))
        
        conn.commit()
        return True # Berhasil insert, berarti unik
        
    except sqlite3.IntegrityError:
        # Gagal insert karena PRIMARY KEY constraint (duplikat)
        return False 
    except Exception as e:
        logging.error(f"Error saat check/insert event {event.event_id}: {e}", exc_info=True)
        # Jika ada error lain, anggap saja gagal proses (lebih aman)
        return False 
    finally:
        if conn:
            conn.close()

# --- FUNGSI BARU UNTUK MEMBACA DATA SAAT STARTUP ---
def get_all_processed_events() -> list[Event]:
    """Mengambil semua event yang sudah diproses dari DB."""
    events = []
    conn = None
    try:
        # Jika file DB tidak ada, kembalikan list kosong
        if not os.path.exists(DB_NAME):
             return []
             
        conn = sqlite3.connect(DB_NAME)
        # Set row_factory agar hasil query bisa diakses seperti dictionary
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        cursor.execute("SELECT topic, event_id, timestamp, source, payload FROM processed_events ORDER BY processed_at ASC")
        rows = cursor.fetchall()
        
        for row in rows:
            try:
                # Deserialize payload dari JSON string
                payload_dict = json.loads(row['payload']) if row['payload'] else {}
                
                # Buat ulang objek Event
                event = Event(
                    topic=row['topic'],
                    event_id=row['event_id'],
                    # Konversi string ISO8601 kembali ke datetime
                    timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else datetime.utcnow(), 
                    source=row['source'],
                    payload=payload_dict
                )
                events.append(event)
            except Exception as parse_error:
                 logging.error(f"Gagal mem-parsing event dari DB: ID={row['event_id']}, Error: {parse_error}", exc_info=True)
                 # Lanjutkan ke baris berikutnya jika satu baris rusak

        logging.info(f"Berhasil memuat {len(events)} event dari database.")
        return events

    except Exception as e:
        logging.error(f"Gagal membaca event dari database: {e}", exc_info=True)
        # Jika gagal baca, kembalikan list kosong (agar server tetap bisa start)
        return [] 
    finally:
        if conn:
            conn.close()
# ----------------------------------------------------