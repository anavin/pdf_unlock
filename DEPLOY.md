# 🚀 Deploy ผ่าน GitHub ไปยัง Cloud ฟรี

คู่มือนี้จะแสดงวิธี deploy app ผ่าน GitHub ไปยัง 3 cloud platforms ฟรี

---

## 📋 ขั้นตอนเริ่มต้น (ทำครั้งเดียว)

### 1. Push code ขึ้น GitHub

```bash
# จาก folder pdf_unlock_webapp
cd pdf_unlock_webapp

# สร้าง git repo
git init
git add .
git commit -m "Initial commit: PDF Password Remover"

# สร้าง repo ใหม่บน GitHub แล้ว copy URL มา
# จากนั้น link กับ remote
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pdf-unlock.git
git push -u origin main
```

---

## 🟢 Option 1: Render (แนะนำ — ง่ายที่สุด)

**ข้อดี:** ตั้งค่าง่ายที่สุด, ไม่ต้องใช้บัตรเครดิต, มี HTTPS อัตโนมัติ
**ข้อเสีย:** Free tier sleep หลังไม่มี traffic 15 นาที (ตื่นช้า ~30 วินาทีตอน request แรก)

### ขั้นตอน

1. ไปที่ [render.com](https://render.com) และ Sign up ด้วย GitHub
2. คลิก **New +** → **Blueprint**
3. เลือก repository ที่เพิ่ง push ขึ้นไป
4. Render จะอ่าน `render.yaml` อัตโนมัติ → คลิก **Apply**
5. รอ build เสร็จ (~3-5 นาที)
6. Render จะให้ URL เช่น `https://pdf-unlock.onrender.com`

**Auto-deploy:** ทุกครั้งที่ `git push` ไปที่ branch `main` → Render จะ build และ deploy ใหม่อัตโนมัติ

### หรือถ้าไม่อยากใช้ Blueprint
1. **New +** → **Web Service**
2. Connect GitHub repo
3. ตั้งค่า:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
   - **Plan:** Free

---

## 🟣 Option 2: Railway

**ข้อดี:** ไม่ sleep, deploy เร็ว, UI สวย
**ข้อเสีย:** Free tier ให้ $5 credit/เดือน (พอใช้สำหรับ app เล็ก), ต้องเพิ่ม payment method หลัง trial หมด

### ขั้นตอน

1. ไปที่ [railway.com](https://railway.com) และ Sign up ด้วย GitHub
2. คลิก **New Project** → **Deploy from GitHub repo**
3. เลือก repository
4. Railway จะอ่าน `railway.json` และใช้ Dockerfile build
5. รอ build เสร็จ (~2-3 นาที)
6. ไปที่ **Settings** → **Networking** → **Generate Domain**
7. จะได้ URL เช่น `https://pdf-unlock-production.up.railway.app`

**Auto-deploy:** Railway watch branch ที่กำหนด — push ใหม่ = deploy ใหม่

---

## 🔵 Option 3: Fly.io

**ข้อดี:** เร็ว, ใกล้ user (มี region สิงคโปร์), free tier ใจดี
**ข้อเสีย:** ต้องใช้ CLI, ต้องเพิ่มบัตรเครดิตยืนยัน (แม้ไม่คิดเงินใน free tier)

### ขั้นตอน

```bash
# 1. ติดตั้ง flyctl CLI
# macOS / Linux:
curl -L https://fly.io/install.sh | sh
# Windows (PowerShell):
# iwr https://fly.io/install.ps1 -useb | iex

# 2. Login
fly auth login

# 3. จาก folder pdf_unlock_webapp
cd pdf_unlock_webapp

# 4. Launch app (จะถามว่าใช้ fly.toml ที่มีไหม → ตอบ Yes)
fly launch --no-deploy

# 5. ถ้าชื่อ pdf-unlock ถูกใช้แล้ว — แก้ใน fly.toml: app = "ชื่อใหม่ของคุณ"

# 6. Deploy
fly deploy

# 7. เปิด app
fly open
```

### Auto-deploy ผ่าน GitHub Actions (Optional)

สร้างไฟล์ `.github/workflows/fly.yml`:

```yaml
name: Fly Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    concurrency: deploy-group
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

แล้วเพิ่ม secret บน GitHub:
```bash
fly tokens create deploy
# Copy token ไปใส่ใน GitHub repo → Settings → Secrets → New repository secret
# Name: FLY_API_TOKEN
```

---

## 📊 เปรียบเทียบ Free Tier

| Feature | Render | Railway | Fly.io |
|---------|--------|---------|--------|
| **ราคาเริ่มต้น** | ฟรี | $5 credit/เดือน | ฟรี (3 VMs) |
| **บัตรเครดิต** | ❌ ไม่ต้อง | ⚠️ หลัง trial | ✅ ต้องยืนยัน |
| **Sleep on idle** | ✅ ใช่ | ❌ ไม่ | ⚙️ ตั้งค่าได้ |
| **Cold start** | ~30s | ทันที | ~2-3s |
| **Region สิงคโปร์** | ✅ | ✅ | ✅ |
| **HTTPS** | อัตโนมัติ | อัตโนมัติ | อัตโนมัติ |
| **Custom domain** | ฟรี | ฟรี | ฟรี |
| **ความยาก** | ⭐ ง่ายสุด | ⭐⭐ ง่าย | ⭐⭐⭐ ปานกลาง |

---

## 🎯 แนะนำให้ใช้ตัวไหน?

- **เริ่มต้น/ทดลอง** → ใช้ **Render** (ไม่ต้องบัตรเครดิต ตั้งค่าง่ายสุด)
- **ต้องการ uptime ดี** → ใช้ **Railway** (ไม่ sleep แต่ต้องเพิ่ม payment method ภายหลัง)
- **ต้องการ performance สูง / latency ต่ำ** → ใช้ **Fly.io**

---

## 🔧 Troubleshooting

### Build ล้มเหลว
- ตรวจสอบ `requirements.txt` ว่าครบ
- ดู build logs บน platform dashboard

### ตอน deploy แล้วเข้าไม่ได้
- ตรวจสอบว่า `--port $PORT` (ไม่ใช่ port คงที่) — cloud platforms ใช้ random port
- Render/Railway ตั้ง env var `PORT` ให้อัตโนมัติ ไม่ต้องตั้งเอง

### อัปโหลดไฟล์ใหญ่ไม่ได้
- Render free tier มี request timeout 100 วินาที
- ถ้าจำเป็น ลด `MAX_FILE_SIZE` ใน `app/main.py`
