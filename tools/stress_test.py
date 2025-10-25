# d. Performa Minimum
# VERSI FINAL: untuk Docker Compose
# Script ini membaca API_URL dari environment variable

import httpx
import asyncio
import uuid
import random
import time
from datetime import datetime
import os # Import os

# --- PENTING ---
# Ambil URL dari environment variable.
# Jika tidak ada, gunakan localhost (untuk tes lokal)
API_URL = os.environ.get("AGGREGATOR_API_URL", "http://127.0.0.1:8080/publish")

# Konfigurasi
TOTAL_EVENTS = 5000
DUPLICATE_PERCENTAGE = 0.20 # 20%
BATCH_SIZE = 100

async def send_batch(client: httpx.AsyncClient, batch: list):
    """Mengirim satu batch event ke API."""
    try:
        response = await client.post(API_URL, json=batch, timeout=30.0)
        response.raise_for_status() # Error jika status 4xx atau 5xx
        print(f"Mengirim {len(batch)} event... OK")
        return len(batch)
    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e.response.status_code} - {e.response.text}")
        return 0
    except httpx.RequestError as e:
        print(f"Request error ke {API_URL}: {e}")
        return 0

async def main():
    print(f"--- Memulai Stress Test ---")
    print(f"Target API: {API_URL}")
    
    # Tunggu sebentar untuk memastikan server benar-benar siap
    if "AGGREGATOR_API_URL" in os.environ:
        print("Menunggu server aggregator (5 detik)...")
        await asyncio.sleep(5)
    
    num_duplicates = int(TOTAL_EVENTS * DUPLICATE_PERCENTAGE)
    num_unique = TOTAL_EVENTS - num_duplicates
    
    print(f"Total Events: {TOTAL_EVENTS}")
    print(f"Unique: {num_unique}, Duplicates: {num_duplicates}")
    
    events_to_send = []
    
    # 1. Buat event unik
    unique_events = []
    for i in range(num_unique):
        event = {
            "topic": random.choice(["auth.prod", "payment.dev", "logs.staging"]),
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "compose_publisher",
            "payload": {"index": i}
        }
        events_to_send.append(event)
        unique_events.append(event)
    
    # 2. Ambil event untuk diduplikasi
    for _ in range(num_duplicates):
        event_to_dupe = random.choice(unique_events)
        events_to_send.append(event_to_dupe)
        
    random.shuffle(events_to_send)
    
    print(f"Total event list generated: {len(events_to_send)} events.")
    print("Mulai mengirim event dalam batch...")
    
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(0, TOTAL_EVENTS, BATCH_SIZE):
            batch = events_to_send[i:i + BATCH_SIZE]
            tasks.append(send_batch(client, batch))
            
        results = await asyncio.gather(*tasks)
        
    end_time = time.time()
    
    total_sent = sum(results)
    
    print("\n--- Stress Test Selesai ---")
    print(f"Total event terkirim: {total_sent}")
    print(f"Waktu eksekusi: {end_time - start_time:.2f} detik")
    print(f"Rata-rata: {total_sent / (end_time - start_time):.2f} events/detik")

if __name__ == "__main__":
    asyncio.run(main())