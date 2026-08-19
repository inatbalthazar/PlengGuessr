# 🎵 SongGuessr

เกมทายเพลงสไตล์ Bandle — แยกเสียงดนตรีอัตโนมัติด้วย Demucs แล้วเล่นแบบ 4-Stem

## โครงสร้างโปรเจกต์

```
SongGuessr/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── models.py            # Pydantic models
│   ├── routers/songs.py     # API endpoints
│   └── services/
│       ├── downloader.py    # yt-dlp + ffmpeg trim
│       ├── separator.py     # Demucs stem separation
│       └── song_store.py    # songs.json R/W
├── frontend/                # React + Vite
│   ├── public/audio/        # {song_id}/*.mp3 (stems)
│   └── src/
│       ├── pages/           # GamePlayer.jsx, Admin.jsx
│       ├── components/      # StemCard, SongTable, ProcessingModal
│       └── hooks/           # useAudioEngine, usePolling
├── songs.json               # Song metadata (flat-file DB)
└── requirements.txt
```

---

## ติดตั้ง Dependencies

### 1. Python (Backend)

> แนะนำให้ใช้ Python 3.10–3.12

```powershell
# สร้าง virtual environment
python -m venv .venv
.venv\Scripts\activate

# ติดตั้ง packages
pip install -r requirements.txt
```

> **หมายเหตุ Torch/Demucs**: ถ้ามี GPU (NVIDIA) ให้ติดตั้ง PyTorch เวอร์ชัน CUDA ก่อน:
> ```
> pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
> ```
> แล้วค่อย `pip install demucs`

---

### 2. FFmpeg (Windows)

ดาวน์โหลด FFmpeg จาก [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)  
หรือติดตั้งผ่าน **winget**:

```powershell
winget install ffmpeg
```

ตรวจสอบ:
```powershell
ffmpeg -version
```

---

### 3. Node.js (Frontend)

```powershell
cd frontend
npm install
```

---

## รันโปรเจกต์ (Development)

ต้องรัน **2 terminal** พร้อมกัน:

### Terminal 1 — Backend

```powershell
# จาก root ของโปรเจกต์
.venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000
```

### Terminal 2 — Frontend

```powershell
cd frontend
npm run dev
```

เปิดเบราว์เซอร์ที่ [http://localhost:5173](http://localhost:5173)

---

## API Endpoints

| Method | Path | คำอธิบาย |
|--------|------|-----------|
| `POST` | `/api/process-song` | เริ่ม pipeline (download → trim → Demucs) |
| `GET` | `/api/status/{task_id}` | ดูสถานะ task (poll ทุก 1.5 วินาที) |
| `GET` | `/api/songs` | ดูรายการเพลงทั้งหมด |
| `DELETE` | `/api/songs/{song_id}` | ลบเพลง + ไฟล์เสียง |

---

## การใช้งาน

### หน้า Admin (`/admin`)
1. วาง YouTube URL หรืออัปโหลดไฟล์ MP3
2. กรอกชื่อเพลง / ศิลปิน / จุดเริ่มต้น / ความยาว
3. กด **"เริ่มแยกเสียงและเพิ่มเพลง"**
4. รอ Modal แสดงความคืบหน้า (Demucs ใช้เวลา 2–10 นาที)

### หน้าเกม (`/`)
1. เลือกเพลงจาก Dropdown
2. รอโหลดเสียง (Web Audio API decode)
3. กด **▶ เล่น** — เริ่มต้น Drums unmuted, Stems อื่น muted
4. คลิกการ์ด Stem หรือกด `1–4` เพื่อเปิด/ปิดเสียง
5. กด **🏆 เฉลยเพลง** หรือ `Enter` เมื่อต้องการเฉลย

### คีย์ลัด
| คีย์ | การทำงาน |
|------|-----------|
| `Space` | เล่น / หยุด |
| `1` | Toggle กลอง (Drums) |
| `2` | Toggle เบส (Bass) |
| `3` | Toggle ดนตรี (Other) |
| `4` | Toggle ร้อง (Vocals) |
| `Enter` | เฉลยเพลง |
| `R` | รีเซ็ต |

---

## Build สำหรับ Production

```powershell
cd frontend
npm run build

# รัน FastAPI เพียง server เดียว (serve React dist)
.venv\Scripts\activate
uvicorn backend.main:app --port 8000
```

เปิดที่ [http://localhost:8000](http://localhost:8000)
# PlengGuessr