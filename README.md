# 🔓 PDF Password Remover

เว็บแอปสำหรับลบ password ออกจากไฟล์ PDF หลายไฟล์พร้อมกัน ผ่านเบราว์เซอร์

## ✨ Features

- 📦 รองรับการอัปโหลดหลายไฟล์พร้อมกัน (สูงสุด 50 ไฟล์)
- 🔑 ลอง password หลายตัวอัตโนมัติ (คั่นด้วย comma)
- 🎨 UI สวยงาม รองรับ drag & drop
- 🔒 ปลอดภัย — ประมวลผลในหน่วยความจำ ไม่บันทึกไฟล์ลงเซิร์ฟเวอร์
- 📥 ดาวน์โหลดผลลัพธ์เป็น ZIP เมื่อมีหลายไฟล์
- 🐳 Deploy ง่ายด้วย Docker

---

## 🚀 วิธี Deploy

### Option 1: รันบนเครื่องตัวเอง (ง่ายสุด)

```bash
# 1. สร้าง virtual environment
python3 -m venv venv
source venv/bin/activate  # บน Windows: venv\Scripts\activate

# 2. ติดตั้ง dependencies
pip install -r requirements.txt

# 3. รัน
uvicorn app.main:app --host 0.0.0.0 --port 8000

# เปิดเบราว์เซอร์ไปที่ http://localhost:8000
```

### Option 2: Docker (แนะนำสำหรับ production)

```bash
# Build และรันด้วย docker-compose
docker compose up -d

# ดู logs
docker compose logs -f

# หยุดเซอร์วิส
docker compose down
```

หรือใช้ Docker โดยตรง:

```bash
docker build -t pdf-unlock .
docker run -d -p 8000:8000 --name pdf-unlock pdf-unlock
```

### Option 3: Deploy ขึ้น Cloud

#### Railway / Render / Fly.io
ทุกแพลตฟอร์มเหล่านี้รองรับ Docker อัตโนมัติ — แค่ push code ไปที่ GitHub และเชื่อม repo

#### Railway

```bash
# ติดตั้ง Railway CLI
npm i -g @railway/cli
railway login
railway init
railway up
```

#### Fly.io

```bash
# ติดตั้ง flyctl
fly launch
fly deploy
```

#### VPS (Ubuntu/Debian) ด้วย Nginx

```bash
# 1. ติดตั้ง dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv nginx

# 2. Clone code และ setup
cd /opt
sudo git clone <your-repo> pdf-unlock
cd pdf-unlock
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. สร้าง systemd service
sudo nano /etc/systemd/system/pdf-unlock.service
```

ใส่เนื้อหานี้:

```ini
[Unit]
Description=PDF Password Remover
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/pdf-unlock
Environment="PATH=/opt/pdf-unlock/venv/bin"
ExecStart=/opt/pdf-unlock/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 4. เริ่ม service
sudo systemctl daemon-reload
sudo systemctl enable pdf-unlock
sudo systemctl start pdf-unlock

# 5. ตั้งค่า Nginx reverse proxy
sudo nano /etc/nginx/sites-available/pdf-unlock
```

ใส่:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;  # อนุญาตอัปโหลดไฟล์ใหญ่

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 6. เปิดใช้งาน
sudo ln -s /etc/nginx/sites-available/pdf-unlock /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 7. (แนะนำ) ตั้งค่า HTTPS ด้วย Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🏗️ โครงสร้าง Project

```
pdf_unlock_webapp/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI backend
├── templates/
│   └── index.html           # หน้า UI
├── static/
│   ├── style.css            # CSS
│   └── app.js               # Frontend JavaScript
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## ⚙️ การตั้งค่า

ค่าจำกัดสามารถปรับได้ใน `app/main.py`:

```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB ต่อไฟล์
MAX_FILES = 50                     # 50 ไฟล์ต่อครั้ง
```

ถ้า deploy หลัง reverse proxy (Nginx/Caddy) อย่าลืมตั้ง `client_max_body_size` ให้สอดคล้องกัน

---

## 🛡️ Security Notes

- ไฟล์ทั้งหมดประมวลผลในหน่วยความจำ ไม่เขียนลงดิสก์
- ใช้ non-root user ใน Docker container
- มี health check endpoint ที่ `/health`
- หากนำไป deploy บน internet ควรเพิ่ม:
  - HTTPS (Let's Encrypt)
  - Rate limiting (Nginx limit_req หรือ Cloudflare)
  - ตั้งค่า CORS ตามต้องการ

---

## 📝 License

MIT
