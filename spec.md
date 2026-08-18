ช่วยสร้างระบบเกมทายเพลง Bandle แบบ Full-stack (สำหรับรัน Local) ที่มีทั้ง "หน้าเล่นเกมสำหรับ Host" และ "หน้า Admin สำหรับเพิ่มเพลงพร้อมระบบแยกเสียงอัตโนมัติ"

### Tech Stack:
- Backend: Python (FastAPI + Uvicorn) ร่วมกับ yt-dlp, ffmpeg-python, demucs
- Frontend: HTML/Tailwind CSS/JavaScript หรือ React (Vite)

### รายละเอียดระบบที่ต้องทำ:

1. Backend API (FastAPI):
   - POST `/api/process-song`:
     * รับข้อมูล: { youtube_url, title, artist, start_time (วินาที), duration (วินาที, ค่าเริ่มต้น 30) } หรือรองรับการอัปโหลดไฟล์เสียง
     * Pipeline การทำงาน:
       1) ใช้ yt-dlp โหลดเสียง และใช้ ffmpeg ตัดตาม start_time & duration ที่ระบุ
       2) รัน Demucs แยกไฟล์เสียงออกมาเป็น 4 stems (drums, bass, other, vocals)
       3) ย้ายไฟล์ผลลัพธ์ไปเก็บที่ `frontend/public/audio/{song_id}/` (แปลงเป็น .mp3 หรือ .wav)
       4) เพิ่ม Object ข้อมูลเพลงใหม่ลงในไฟล์ `songs.json` อัตโนมัติ
     * ส่ง Response แจ้งสถานะความสำเร็จกลับมา

2. Frontend - หน้า Admin (/admin):
   - มีฟอร์มกรอก:
     * ลิงก์ YouTube หรือ อัปโหลดไฟล์ MP3
     * ชื่อเพลง (Title) & ชื่อศิลปิน (Artist)
     * จุดเริ่มต้น (Start time เช่น 00:15) และ ความยาว (Duration เช่น 30s)
   - ปุ่ม "เริ่มแยกเสียงและเพิ่มเพลง" พร้อมแสดง Loading Spinner / Progress ระหว่างที่ Backend กำลังรัน Demucs
   - แสดงตารางรายการเพลงทั้งหมดที่มีใน `songs.json` พร้อมปุ่มกดฟังพรีวิวแต่ละ Stem และปุ่มลบเพลง

3. Frontend - หน้า Game Player (/):
   - หน้า UI เล่นเกมสำหรับ Host แชร์จอ (ซิงค์เล่น 4 Stems พร้อมกัน, ควบคุม Mute/Unmute ทีละเครื่องดนตรี, มีปุ่มเฉลยและคีย์ลัด)

ช่วยเขียนโค้ด Backend, Frontend, requirements.txt, โครงสร้างโฟลเดอร์ และคำสั่งวิธีติดตั้ง FFmpeg/Demucs สำหรับรันโปรเจกต์นี้