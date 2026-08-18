from pydantic import BaseModel
from typing import Optional, Dict, Any


class StemPaths(BaseModel):
    drums: str
    bass: str
    other: str
    vocals: str


class Song(BaseModel):
    id: str
    title: str
    artist: str
    stems: Dict[str, str]


class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending | downloading | separating | saving | done | error
    progress: int  # 0–100
    message: str
    song: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
