# src/models.py
# VERSI FINAL (FIXED 2) - dengan perbaikan 'ConfigDict'

from pydantic import BaseModel, Field, ConfigDict # <- Impor ConfigDict
from datetime import datetime
from typing import Dict, Any
import uuid

class Event(BaseModel):
    """
    Model data Pydantic untuk event log.
    Ini akan otomatis memvalidasi skema JSON yang masuk.
    """
    topic: str
    
    # Jika event_id tidak disediakan, buat UUIDv4 baru secara otomatis
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Jika timestamp tidak disediakan, gunakan waktu saat ini (UTC)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    source: str
    
    # payload biarkan fleksibel, bisa berisi JSON apa saja
    payload: Dict[str, Any]

    # --- PERBAIKAN DI SINI ---
    # Mengganti 'class Config' yang usang dengan 'model_config'
    model_config = ConfigDict(
        from_attributes=True
    )