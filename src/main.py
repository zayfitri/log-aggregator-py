# src/main.py
# VERSI FINAL (FIXED 3) - Membaca data dari DB saat startup

from fastapi import FastAPI, HTTPException, Request
from typing import List, Union, Dict, Any
import asyncio
import time
import logging
from contextlib import asynccontextmanager

from .models import Event
# --- PERUBAHAN DI SINI ---
from .database import setup_database, check_and_insert_event, get_all_processed_events # Impor fungsi baru
# -------------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- State Aplikasi (Global) ---
# Dikosongkan dulu, akan diisi saat startup
event_queue = asyncio.Queue()
unique_events_storage: List[Event] = [] 
stats = {
    "start_time": time.time(),
    "received": 0, # Received akan selalu mulai dari 0 setiap restart
    "unique_processed": 0, # Akan diisi dari DB
    "duplicate_dropped": 0, # Tidak bisa dihitung ulang, mulai dari 0
    "topics": set() # Akan diisi dari DB
}
# --- End of State ---


# --- Background Consumer Task (Sama seperti versi FIXED 2) ---
async def consumer_task(queue: asyncio.Queue): 
    logging.info("Consumer task dimulai...")
    while True:
        try:
            event = await queue.get() 
            is_unique = check_and_insert_event(event)
            
            if is_unique:
                logging.info(f"Event UNIK diproses: (Topic: {event.topic}, ID: {event.event_id})")
                stats["unique_processed"] += 1
                stats["topics"].add(event.topic)
                unique_events_storage.append(event) 
            else:
                logging.info(f"Event DUPLIKAT terdeteksi: (Topic: {event.topic}, ID: {event.event_id})")
                stats["duplicate_dropped"] += 1
            
            queue.task_done() 

        except asyncio.CancelledError:
            logging.info("Consumer task dihentikan.")
            break
        except Exception as e:
            if "is bound to a different event loop" in str(e):
                 logging.error(f"FATAL: Consumer task mendeteksi masalah event loop dengan queue!")
            else:
                 logging.error(f"Error di consumer task: {e}", exc_info=True)
            await asyncio.sleep(1) 

# --- Lifespan (Startup & Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Server startup... Menyiapkan database.")
    setup_database()
    
    # --- PERUBAHAN UTAMA DI SINI ---
    logging.info("Memuat data event yang sudah diproses dari database...")
    # 1. Baca semua event lama dari DB
    loaded_events = get_all_processed_events() 
    # 2. Isi kembali state di memori
    unique_events_storage.extend(loaded_events)
    stats["unique_processed"] = len(loaded_events)
    stats["topics"] = set(event.topic for event in loaded_events)
    logging.info(f"Startup selesai. {stats['unique_processed']} event unik dimuat.")
    # -----------------------------
    
    consumer = asyncio.create_task(consumer_task(event_queue)) 
    logging.info("Consumer task telah dijadwalkan.")
    
    yield 
    
    logging.info("Server shutdown...")
    consumer.cancel()
    try:
        await asyncio.wait_for(event_queue.join(), timeout=5.0) 
    except asyncio.TimeoutError:
        logging.warning("Timeout saat menunggu queue kosong, shutdown paksa.")
    logging.info("Shutdown selesai.")

# --- Aplikasi FastAPI (Sama) ---
app = FastAPI(
    title="UTS Pub-Sub Log Aggregator",
    description="Layanan aggregator log dengan idempotent consumer dan deduplikasi.",
    version="1.0.0",
    lifespan=lifespan
)

# --- Endpoint API (Sama) ---
@app.post("/publish", status_code=202)
async def publish_events(payload: Union[Event, List[Event]]):
    events_to_process = []
    if isinstance(payload, Event):
        events_to_process.append(payload)
    else:
        events_to_process = payload
    
    for event in events_to_process:
        stats["received"] += 1
        await event_queue.put(event) 
    
    return {"message": f"{len(events_to_process)} event(s) diterima untuk diproses"}

@app.get("/stats", response_model=Dict[str, Any])
async def get_stats():
    # 'received' dan 'duplicate_dropped' mungkin tidak akurat setelah restart
    # tapi 'unique_processed' dan 'topics' akan akurat dari DB
    return {
        "uptime_seconds": round(time.time() - stats["start_time"], 2),
        "received_total (since_restart)": stats["received"], # Ganti nama agar jelas
        "unique_processed (total)": stats["unique_processed"], # Ini dari DB
        "duplicate_dropped (since_restart)": stats["duplicate_dropped"], # Ganti nama
        "topics_list (total)": list(stats["topics"]) # Ini dari DB
    }

@app.get("/events", response_model=List[Event])
async def get_events(topic: str = None):
    # Sekarang list ini diisi dari DB saat startup
    if topic:
        return [event for event in unique_events_storage if event.topic == topic]
    return unique_events_storage

@app.get("/")
async def root():
    return {"message": "Log Aggregator Service. Kunjungi /docs untuk dokumentasi API."}