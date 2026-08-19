# 🚀 PlengGuessr — คู่มือการ Deploy และอัปเดตเพลงออนไลน์

โปรเจกต์นี้ได้รับการตั้งค่าสำหรับการ Deploy เป็น **Static Online Web App** บน **Cloudflare Pages** หรือ **Vercel** เรียบร้อยแล้ว (ฟรี 100% ประสิทธิภาพสูง โหลดเร็วทั่วโลก)

---

## 🛠️ สิ่งที่ระบบเตรียมไว้ให้แล้ว

1. **`vercel.json`**: ตั้งค่า Build Command และ SPA Rewrites สำหรับ Vercel
2. **`frontend/public/_redirects`**: ตั้งค่า SPA Routing สำหรับ Cloudflare Pages / Netlify (ไม่เกิดปัญหา 404 เมื่อกดรีเฟรชหน้า `/admin`)
3. **Auto Static Sync (`copy-json`)**: สคริปต์อัตโนมัติที่ซิงค์ `songs.json` และ `playlists.json` เข้าโฟลเดอร์ build ทุกครั้งที่สั่ง `npm run build`
4. **Static Fallback**: โค้ด Frontend จะโหลดข้อมูลผ่าน `/api` ก่อน หากไม่พบ Backend ออนไลน์ จะสลับไปอ่านจาก `songs.json` และ `playlists.json` อัตโนมัติ

---

## 📌 ขั้นตอนการ Deploy ขึ้น Cloudflare Pages หรือ Vercel

### วิธีที่ 1: Deploy ผ่าน Cloudflare Pages (แนะนำที่สุด — ฟรี ไม่จำกัด Bandwidth)

1. **Push โค้ดขึ้น GitHub**:
   ```bash
   git add .
   git commit -m "Prepare deployment for Cloudflare Pages / Vercel"
   git push origin main
   ```
2. สมัคร/เข้าสู่ระบบ [Cloudflare Dashboard](https://dash.cloudflare.com/) -> ไปที่ **Workers & Pages** -> **Create application** -> **Pages** -> **Connect to Git**
3. เลือก Repository `PlengGuessr`
4. กรอกข้อมูลตั้งค่า Build Settings:
   * **Framework preset**: `Vite` (หรือ None)
   * **Build command**: `cd frontend && npm install && npm run build`
   * **Build output directory**: `frontend/dist`
5. กด **Save and Deploy** — รอประมาณ 1–2 นาที เว็บจะพร้อมใช้งานออนไลน์ทันที!

> 💡 **หาก Deploy ผ่าน Wrangler CLI (Build & Deploy Command ใน Cloudflare Pages)**:
> - **Build Command**: `cd frontend && npm install && npm run build`
> - **Deploy Command**: `npx wrangler pages deploy frontend/dist --project-name plengguessr2`

---

### วิธีที่ 2: Deploy ผ่าน Vercel

1. Push โค้ดขึ้น GitHub
2. เข้าสู่ระบบ [Vercel](https://vercel.com/) -> กด **Add New...** -> **Project**
3. Import Repository `PlengGuessr`
4. Vercel จะตรวจพบ `vercel.json` โดยอัตโนมัติ กด **Deploy**
5. เสร็จสิ้น! เว็บออนไลน์พร้อมใช้งาน

---

## 🎶 วิธีเพิ่มเพลงใหม่ไปที่ Database ออนไลน์ในภายหลัง

เนื่องจากการแยก Stem ด้วย **Demucs** ต้องใช้ CPU/GPU และ RAM สูง การประมวลผลจึงทำที่ **เครื่องคอมพิวเตอร์ของคุณ (Local)** แล้วซิงค์ขึ้น Cloud มีขั้นตอนง่ายๆ 4 ขั้นตอนดังนี้:

### ขั้นตอนการเพิ่มเพลง:

1. **ใส่รายชื่อเพลงที่ต้องการเพิ่ม**:
   เปิดไฟล์ `playlist.txt` แล้วเพิ่มรายชื่อเพลงในรูปแบบ `ชื่อศิลปิน - ชื่อเพลง` เช่น:
   ```text
   Bodyslam - แสงสุดท้าย
   Bruno Mars - Apt.
   ```

2. **ประมวลผลแยก Stem เสียง (Demucs)**:
   เปิด Terminal ที่โฟลเดอร์โปรเจกต์ แล้วรัน:
   ```powershell
   python batch_process.py
   ```
   *(สคริปต์จะค้นหา YouTube, ดาวน์โหลด, ตัดคลิป, แยก 4 Stems ด้วย Demucs และบันทึกลง `songs.json` อัตโนมัติ)*

3. **จัดหมวดหมู่ Playlist / Quiz**:
   รันสคริปต์จัดกลุ่มเพลงลงใน Playlists (สากล, ไทย, K-Pop):
   ```powershell
   python create_playlists.py
   ```

4. **Push ขึ้น GitHub (Auto-Deploy)**:
   ```powershell
   git add .
   git commit -m "Add new songs to database"
   git push origin main
   ```

⚡ **เมื่อ push เสร็จแล้ว Cloudflare Pages หรือ Vercel จะ Build และเพิ่มเพลงใหม่เข้าสู่เว็บออนไลน์ให้ผู้เล่นทันทีอัตโนมัติ!**
