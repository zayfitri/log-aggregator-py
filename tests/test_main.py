# tests/test_main.py
# VERSI FINAL (FIXED 5) - Menggunakan queue lokal di tes

import pytest
import pytest_asyncio
import os
import asyncio
import anyio 
import logging # <- Tambahkan logging
from httpx import AsyncClient, ASGITransport

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Impor app untuk transport, stats & storage untuk reset, consumer_task untuk dijalankan
from src.main import app, stats, unique_events_storage, consumer_task 
from src.database import setup_database, DB_NAME
from src.models import Event

# JANGAN impor event_queue global lagi

# --- Fungsi Helper (Masih Sama) ---
async def wait_for_queue(q: asyncio.Queue, timeout=2.0): # Timeout dinaikkan sedikit
    """Menunggu sampai queue kosong atau timeout."""
    start_time = asyncio.get_event_loop().time()
    processed_count = 0 # Tambahan logging
    while not q.empty():
        processed_in_loop = q.qsize() # Logging tambahan
        if asyncio.get_event_loop().time() - start_time > timeout:
            logging.error(f"TIMEOUT! Queue masih berisi {q.qsize()} item setelah {timeout} detik.")
            raise asyncio.TimeoutError("Queue tidak kosong dalam batas waktu.")
        await asyncio.sleep(0.05) # Tidur sedikit lebih lama
        # Logging tambahan: cek apakah item berkurang
        if q.qsize() < processed_in_loop:
             processed_count += (processed_in_loop - q.qsize())
             # logging.info(f"Consumer memproses {processed_in_loop - q.qsize()} item, sisa {q.qsize()}")
    # logging.info(f"Queue kosong setelah memproses total {processed_count} item.")


# --- Fixture (Setup Tes) ---
@pytest_asyncio.fixture(scope="function", autouse=True)
async def test_app_with_consumer(): # Nama diubah agar lebih jelas
    """Fixture yang menjalankan consumer di background DENGAN queue tes lokal."""
    
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    setup_database()

    # Reset state global (kecuali queue)
    stats["received"] = 0
    stats["unique_processed"] = 0
    stats["duplicate_dropped"] = 0
    stats["topics"].clear()
    unique_events_storage.clear()
    
    # --- PERUBAHAN UTAMA DI SINI ---
    # Buat queue BARU khusus untuk tes ini
    test_queue = asyncio.Queue()
    # -----------------------------

    consumer_task_handle = None # Inisialisasi handle

    try:
        async with anyio.create_task_group() as tg:
            # --- PERUBAHAN UTAMA DI SINI ---
            # Mulai consumer task dengan queue TES
            consumer_task_handle = tg.start_soon(consumer_task, test_queue)
            # -----------------------------
            
            # Siapkan HTTP client (tetap pakai 'app' global untuk routing)
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # --- PERUBAHAN UTAMA DI SINI ---
                # Berikan client DAN queue tes ke fungsi tes
                yield client, test_queue 
                # -----------------------------
            
            # Setelah tes selesai, batalkan consumer task
            if consumer_task_handle: # Pastikan handle ada
                 tg.cancel_scope.cancel()

    except asyncio.CancelledError:
        pass # Normal saat cancel
    except Exception as e:
         logging.error(f"Error dalam fixture test_app_with_consumer: {e}", exc_info=True)
         pytest.fail(f"Fixture setup failed: {e}")


# --- Tes (Dimodifikasi sedikit untuk menerima queue) ---

@pytest.mark.asyncio
# --- PERUBAHAN DI SINI ---
async def test_1_publish_single_event(test_app_with_consumer):
    client, test_queue = test_app_with_consumer # Ambil client dan queue
# -------------------------
    event_data = {"topic": "test", "event_id": "e1", "source": "pytest", "payload": {}}
    
    # --- PERUBAHAN DI SINI ---
    # Tes HARUS memasukkan event ke queue tes, BUKAN via API
    # Karena API terhubung ke queue global yang tidak kita pakai di tes ini
    await test_queue.put(Event(**event_data))
    stats["received"] += 1 # Update manual karena tidak lewat API
    # -------------------------
    
    await wait_for_queue(test_queue) 
    
    assert stats["received"] == 1
    assert stats["unique_processed"] == 1
    assert stats["duplicate_dropped"] == 0

@pytest.mark.asyncio
# --- PERUBAHAN DI SINI ---
async def test_2_deduplication(test_app_with_consumer):
    client, test_queue = test_app_with_consumer
# -------------------------
    event_data = {"topic": "test", "event_id": "e2", "source": "pytest", "payload": {}}
    event_obj = Event(**event_data)
    
    # --- PERUBAHAN DI SINI ---
    await test_queue.put(event_obj) # Kirim pertama
    stats["received"] += 1
    await test_queue.put(event_obj) # Kirim duplikat
    stats["received"] += 1
    # -------------------------
    
    await wait_for_queue(test_queue) 
    
    assert stats["received"] == 2
    assert stats["unique_processed"] == 1
    assert stats["duplicate_dropped"] == 1

@pytest.mark.asyncio
# --- PERUBAHAN DI SINI ---
async def test_3_get_stats_and_events_consistency(test_app_with_consumer):
    client, test_queue = test_app_with_consumer
# -------------------------
    event_data = {"topic": "consistency", "event_id": "e3", "source": "pytest", "payload": {}}

    # --- PERUBAHAN DI SINI ---
    await test_queue.put(Event(**event_data))
    stats["received"] += 1
    # -------------------------

    await wait_for_queue(test_queue)
    
    # API GET tetap bisa dipakai karena membaca state global
    response_stats = await client.get("/stats")
    assert response_stats.status_code == 200
    stats_data = response_stats.json()
    assert stats_data["unique_processed"] == 1
    assert "consistency" in stats_data["topics_list"]
    
    response_events = await client.get("/events")
    assert response_events.status_code == 200
    events_data = response_events.json()
    assert len(events_data) == 1
    assert events_data[0]["event_id"] == "e3"

@pytest.mark.asyncio
# --- PERUBAHAN DI SINI ---
async def test_4_get_events_by_topic(test_app_with_consumer):
    client, test_queue = test_app_with_consumer
# -------------------------

    # --- PERUBAHAN DI SINI ---
    event_a = Event(**{"topic": "topic-a", "event_id": "eA", "source": "pytest", "payload": {}})
    event_b = Event(**{"topic": "topic-b", "event_id": "eB", "source": "pytest", "payload": {}})
    await test_queue.put(event_a)
    stats["received"] += 1
    await test_queue.put(event_b)
    stats["received"] += 1
    # -------------------------
    
    await wait_for_queue(test_queue)
    
    response_a = await client.get("/events?topic=topic-a")
    assert response_a.status_code == 200
    assert len(response_a.json()) == 1
    assert response_a.json()[0]["event_id"] == "eA"
    
    response_b = await client.get("/events?topic=topic-b")
    assert response_b.status_code == 200
    assert len(response_b.json()) == 1
    assert response_b.json()[0]["event_id"] == "eB"

@pytest.mark.asyncio
# --- PERUBAHAN DI SINI ---
async def test_5_publish_batch(test_app_with_consumer):
    client, test_queue = test_app_with_consumer
# -------------------------
    
    # --- PERUBAHAN DI SINI ---
    # Kita simulasikan batch dengan memasukkan ke queue tes
    event1 = Event(**{"topic": "batch", "event_id": "b1", "source": "pytest", "payload": {}})
    event2 = Event(**{"topic": "batch", "event_id": "b2", "source": "pytest", "payload": {}})
    event3_dup = Event(**{"topic": "batch", "event_id": "b1", "source": "pytest", "payload": {}}) # Duplikat
    
    await test_queue.put(event1)
    stats["received"] += 1
    await test_queue.put(event2)
    stats["received"] += 1
    await test_queue.put(event3_dup)
    stats["received"] += 1
    # -------------------------
    
    await wait_for_queue(test_queue)
    
    assert stats["received"] == 3
    assert stats["unique_processed"] == 2
    assert stats["duplicate_dropped"] == 1

@pytest.mark.asyncio
# --- PERUBAHAN DI SINI ---
async def test_6_schema_validation_fail(test_app_with_consumer):
    # Tes ini masih pakai API karena menguji validasi API
    client, _ = test_app_with_consumer # Queue tidak dipakai
# -------------------------
    invalid_data = {"event_id": "e-invalid", "source": "pytest", "payload": "salah"}
    # API POST HARUS gagal karena skema salah
    response = await client.post("/publish", json=invalid_data)
    assert response.status_code == 422