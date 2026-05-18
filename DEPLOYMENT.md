# คู่มือการ Deploy — SmartTextToSpeech

> เอกสารนี้ครอบคลุมการติดตั้งบน **Linux (Ubuntu/Debian)** เป็นหลัก
> และ **Windows Server** เป็นตัวเลือกสำรอง

---

## สารบัญ

1. [ข้อกำหนดของระบบ](#1-ข้อกำหนดของระบบ)
2. [โครงสร้างไฟล์ที่ต้อง Deploy](#2-โครงสร้างไฟล์ที่ต้อง-deploy)
3. [Linux — Ubuntu / Debian (แนะนำ)](#3-linux--ubuntu--debian-แนะนำ)
4. [Windows Server](#4-windows-server)
5. [การตั้งค่า HTTPS / SSL](#5-การตั้งค่า-https--ssl)
6. [การดูแลรักษาระบบ](#6-การดูแลรักษาระบบ)
7. [Checklist ก่อน Go-Live](#7-checklist-ก่อน-go-live)
8. [การแก้ปัญหาเบื้องต้น](#8-การแก้ปัญหาเบื้องต้น)

---

## 1. ข้อกำหนดของระบบ

### Hardware ขั้นต่ำ

| รายการ | ขั้นต่ำ | แนะนำ |
|--------|--------|-------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 1 GB | 2 GB |
| Storage | 10 GB | 20 GB |
| Network | ต้องมีอินเทอร์เน็ต (ใช้ Edge TTS API) | — |

> **สำคัญ:** edge-tts เชื่อมต่อกับ Microsoft Edge TTS Server ทุกครั้งที่สร้างเสียง
> Server ต้องสามารถเข้าถึงอินเทอร์เน็ตได้เสมอ

### Software

| รายการ | เวอร์ชัน |
|--------|---------|
| Python | 3.10 ขึ้นไป |
| OS (Linux) | Ubuntu 22.04 LTS / Debian 12 |
| OS (Windows) | Windows Server 2019/2022 |
| Web Server | Nginx 1.18+ (Linux) / IIS 10+ (Windows) |
| WSGI Server | Gunicorn 21+ (Linux) / Waitress 3+ (Windows) |

---

## 2. โครงสร้างไฟล์ที่ต้อง Deploy

```
smarttexttospeech/
├── app.py                  ← Flask application (หลัก)
├── wsgi.py                 ← Entry point สำหรับ Gunicorn/Waitress
├── gunicorn.conf.py        ← การตั้งค่า Gunicorn (Linux)
├── requirements.txt        ← Python dependencies
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css
│   └── js/app.js
└── audio/                  ← โฟลเดอร์นี้สร้างเองอัตโนมัติ
```

ไฟล์ใน `deploy/` เป็น template สำหรับ config ของ server:

```
deploy/
├── smarttexttospeech.service   ← systemd service (Linux)
└── nginx.conf                  ← Nginx virtual host (Linux)
```

---

## 3. Linux — Ubuntu / Debian (แนะนำ)

### ขั้นตอนที่ 1 — อัปเดตระบบและติดตั้ง dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx git
```

ตรวจสอบเวอร์ชัน Python:

```bash
python3 --version   # ต้องได้ 3.10 ขึ้นไป
```

---

### ขั้นตอนที่ 2 — อัปโหลดไฟล์โปรเจกต์

```bash
# สร้างโฟลเดอร์สำหรับ app
sudo mkdir -p /var/www/smarttexttospeech
sudo chown $USER:$USER /var/www/smarttexttospeech
```

อัปโหลดไฟล์จากเครื่อง Windows ขึ้นไป Server:

```bash
# วิธีที่ 1: ใช้ scp (จากเครื่อง Windows)
scp -r C:\xampp\htdocs\smarttexttospeech\* user@your-server-ip:/var/www/smarttexttospeech/

# วิธีที่ 2: ใช้ rsync
rsync -avz --exclude='audio/' C:\xampp\htdocs\smarttexttospeech/ user@your-server-ip:/var/www/smarttexttospeech/

# วิธีที่ 3: ถ้าใช้ Git
cd /var/www/smarttexttospeech
git clone https://your-repo-url.git .
```

---

### ขั้นตอนที่ 3 — สร้าง Python Virtual Environment

```bash
cd /var/www/smarttexttospeech

# สร้าง venv
python3 -m venv venv

# เปิดใช้งาน venv
source venv/bin/activate

# ติดตั้ง dependencies + Gunicorn
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# ทดสอบว่า import ได้
python -c "import flask, edge_tts; print('OK')"

# ปิด venv
deactivate
```

---

### ขั้นตอนที่ 4 — สร้าง Log Directory

```bash
sudo mkdir -p /var/log/smarttexttospeech
sudo chown www-data:www-data /var/log/smarttexttospeech
```

---

### ขั้นตอนที่ 5 — ตั้งค่า Permission

```bash
# ให้ www-data เป็นเจ้าของไฟล์
sudo chown -R www-data:www-data /var/www/smarttexttospeech

# กำหนด permission
sudo chmod -R 755 /var/www/smarttexttospeech
sudo chmod -R 775 /var/www/smarttexttospeech/audio   # เขียนได้สำหรับ gunicorn worker
```

---

### ขั้นตอนที่ 6 — แก้ไข gunicorn.conf.py

เปิดไฟล์ `/var/www/smarttexttospeech/gunicorn.conf.py` แล้วตรวจสอบ:

```bash
sudo nano /var/www/smarttexttospeech/gunicorn.conf.py
```

ค่าที่ต้องตรวจ:

```python
bind         = "127.0.0.1:5000"   # ฟังเฉพาะ localhost เท่านั้น (Nginx จะ proxy ให้)
workers      = 2                   # ปรับตาม CPU: (2 × vCPU) + 1
timeout      = 120                 # สำคัญ: TTS ใช้เวลานาน อย่าตั้งน้อยกว่า 60
accesslog    = "/var/log/smarttexttospeech/access.log"
errorlog     = "/var/log/smarttexttospeech/error.log"
```

---

### ขั้นตอนที่ 7 — ตั้งค่า systemd Service

```bash
# คัดลอก service file
sudo cp /var/www/smarttexttospeech/deploy/smarttexttospeech.service \
        /etc/systemd/system/smarttexttospeech.service

# โหลด systemd และเปิดใช้งาน service
sudo systemctl daemon-reload
sudo systemctl enable smarttexttospeech
sudo systemctl start smarttexttospeech

# ตรวจสอบสถานะ
sudo systemctl status smarttexttospeech
```

ผลที่ควรเห็น:

```
● smarttexttospeech.service - SmartTextToSpeech — Thai TTS Application
     Loaded: loaded (/etc/systemd/system/smarttexttospeech.service; enabled)
     Active: active (running) since ...
```

ทดสอบว่า Gunicorn ตอบสนอง:

```bash
curl http://127.0.0.1:5000/api/languages
# ต้องได้ JSON กลับมา
```

---

### ขั้นตอนที่ 8 — ตั้งค่า Nginx

```bash
# คัดลอก Nginx config
sudo cp /var/www/smarttexttospeech/deploy/nginx.conf \
        /etc/nginx/sites-available/smarttexttospeech

# แก้ไข server_name ให้ตรงกับ domain จริง
sudo nano /etc/nginx/sites-available/smarttexttospeech
# แก้บรรทัด: server_name your-domain.com;

# เปิดใช้งาน virtual host
sudo ln -s /etc/nginx/sites-available/smarttexttospeech \
           /etc/nginx/sites-enabled/

# ลบ default site (ถ้าไม่ต้องการ)
sudo rm -f /etc/nginx/sites-enabled/default

# ตรวจสอบ config syntax
sudo nginx -t

# โหลด Nginx ใหม่
sudo systemctl reload nginx
```

---

### ขั้นตอนที่ 9 — ตั้งค่า Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'   # เปิด port 80 และ 443
sudo ufw enable
sudo ufw status
```

---

### ขั้นตอนที่ 10 — ทดสอบ End-to-End

```bash
# ทดสอบผ่าน curl
curl -X POST http://your-domain.com/api/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"สวัสดีครับ","voice":"th-TH-PremwadeeNeural","rate":0,"pitch":0}'

# ถ้าได้ {"success": true, ...} แสดงว่าทำงานปกติ
```

เปิดเบราว์เซอร์ไปที่ `http://your-domain.com` แล้วทดสอบสร้างเสียง

---

## 4. Windows Server

> ใช้เมื่อ Server เป็น Windows Server 2019/2022

### ขั้นตอนที่ 1 — ติดตั้ง Python

1. ดาวน์โหลด Python 3.12 จาก [python.org](https://www.python.org/downloads/)
2. ติดตั้งโดยเลือก ✅ **"Add Python to PATH"**
3. ตรวจสอบ: เปิด Command Prompt แล้วรัน `python --version`

### ขั้นตอนที่ 2 — วางไฟล์โปรเจกต์

```powershell
# สร้างโฟลเดอร์
New-Item -ItemType Directory -Force "C:\www\smarttexttospeech"

# คัดลอกไฟล์ (จากเครื่อง dev หรือ unzip)
# ไฟล์ที่ต้องการ: app.py, wsgi.py, requirements.txt, templates/, static/
```

### ขั้นตอนที่ 3 — ติดตั้ง Dependencies

เปิด PowerShell ในฐานะ Administrator:

```powershell
cd C:\www\smarttexttospeech

# สร้าง Virtual Environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# ติดตั้ง packages + Waitress (WSGI server สำหรับ Windows)
pip install -r requirements.txt
pip install waitress

# ทดสอบ
python -c "import flask, edge_tts, waitress; print('OK')"
```

### ขั้นตอนที่ 4 — สร้าง Startup Script

สร้างไฟล์ `C:\www\smarttexttospeech\start.ps1`:

```powershell
# start.ps1 — ใช้รัน Waitress แทน Flask dev server
Set-Location "C:\www\smarttexttospeech"
.\venv\Scripts\Activate.ps1
waitress-serve --listen=127.0.0.1:5000 wsgi:app
```

### ขั้นตอนที่ 5 — ติดตั้ง NSSM (Windows Service Manager)

ดาวน์โหลด NSSM จาก [nssm.cc](https://nssm.cc/download) แล้ววางไฟล์ `nssm.exe` ไว้ที่ `C:\Windows\System32\`

```powershell
# ติดตั้งเป็น Windows Service
nssm install SmartTTS "C:\www\smarttexttospeech\venv\Scripts\waitress-serve.exe"
nssm set SmartTTS AppParameters "--listen=127.0.0.1:5000 wsgi:app"
nssm set SmartTTS AppDirectory "C:\www\smarttexttospeech"
nssm set SmartTTS DisplayName "SmartTextToSpeech"
nssm set SmartTTS Start SERVICE_AUTO_START

# เริ่ม service
nssm start SmartTTS

# ตรวจสอบ
nssm status SmartTTS
```

### ขั้นตอนที่ 6 — ตั้งค่า IIS Reverse Proxy

1. เปิด **IIS Manager**
2. ติดตั้ง module ที่จำเป็น:
   ```powershell
   # ติดตั้ง URL Rewrite Module และ Application Request Routing
   # ดาวน์โหลดจาก: https://www.iis.net/downloads/microsoft/url-rewrite
   # และ: https://www.iis.net/downloads/microsoft/application-request-routing
   ```
3. เปิด **Application Request Routing** → Enable proxy
4. สร้าง Website ใหม่ใน IIS ชี้ไปที่ `C:\www\smarttexttospeech\static`
5. เพิ่ม URL Rewrite rule เพื่อ proxy ไปที่ `http://127.0.0.1:5000`

หรือใช้ **Apache for Windows** (ง่ายกว่า) โดยเพิ่ม VirtualHost เหมือนกับที่ทำบน dev machine:

```apache
<VirtualHost *:80>
    ServerName your-domain.com
    ProxyPreserveHost On
    ProxyPass        / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/
</VirtualHost>
```

---

## 5. การตั้งค่า HTTPS / SSL

> แนะนำอย่างยิ่งสำหรับ production — ใช้ Let's Encrypt (ฟรี)

```bash
# ติดตั้ง Certbot (Linux/Nginx)
sudo apt install -y certbot python3-certbot-nginx

# ขอใบรับรองและตั้งค่า Nginx อัตโนมัติ
sudo certbot --nginx -d your-domain.com

# ทดสอบ auto-renewal
sudo certbot renew --dry-run
```

ใบรับรองจะต่ออายุอัตโนมัติผ่าน cron ที่ Certbot ตั้งให้

---

## 6. การดูแลรักษาระบบ

### คำสั่งที่ใช้บ่อย (Linux)

```bash
# ดู log แบบ real-time
sudo tail -f /var/log/smarttexttospeech/error.log
sudo tail -f /var/log/nginx/smarttexttospeech-error.log

# Restart หลังแก้ไขโค้ด
sudo systemctl restart smarttexttospeech

# ดูสถานะ
sudo systemctl status smarttexttospeech

# Stop / Start
sudo systemctl stop smarttexttospeech
sudo systemctl start smarttexttospeech
```

### อัปเดตโค้ด

```bash
cd /var/www/smarttexttospeech

# อัปโหลดไฟล์ใหม่ (หรือ git pull)
git pull origin main

# อัปเดต dependencies (ถ้ามีการเปลี่ยนแปลง)
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Fix permissions
sudo chown -R www-data:www-data /var/www/smarttexttospeech

# Restart
sudo systemctl restart smarttexttospeech
```

### ตรวจสอบ Disk Space

ไฟล์ MP3 จะถูกลบอัตโนมัติทุก 1 ชั่วโมง แต่ควรตรวจสอบเป็นครั้งคราว:

```bash
# ดูขนาดโฟลเดอร์ audio
du -sh /var/www/smarttexttospeech/audio/

# ดู disk ทั้งหมด
df -h /
```

### Log Rotation

สร้างไฟล์ `/etc/logrotate.d/smarttexttospeech`:

```
/var/log/smarttexttospeech/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    postrotate
        systemctl reload smarttexttospeech
    endscript
}
```

---

## 7. Checklist ก่อน Go-Live

### ความปลอดภัย

- [ ] Firewall เปิดเฉพาะ port 80, 443, และ SSH
- [ ] Gunicorn bind เฉพาะ `127.0.0.1` (ไม่เปิด 0.0.0.0)
- [ ] ไม่รัน Flask ด้วย `debug=True` บน production
- [ ] HTTPS ถูกตั้งค่าแล้ว (Let's Encrypt)
- [ ] Nginx มี security headers (ดูใน `deploy/nginx.conf`)

### การทำงาน

- [ ] `systemctl status smarttexttospeech` แสดง `active (running)`
- [ ] `nginx -t` ผ่านโดยไม่มี error
- [ ] `curl http://localhost:5000/api/languages` ได้ JSON กลับมา
- [ ] ทดสอบสร้างเสียงภาษาไทยได้ปกติ
- [ ] ทดสอบดาวน์โหลด MP3 ได้
- [ ] เปิดบนมือถือ (responsive design) ทำงานได้

### การ Monitor

- [ ] Log files ถูกสร้างและมีข้อมูล
- [ ] ตั้ง Log Rotation แล้ว
- [ ] มีวิธีแจ้งเตือนถ้า service ล่ม (ใช้ UptimeRobot หรือ similar)

---

## 8. การแก้ปัญหาเบื้องต้น

### 502 Bad Gateway

Nginx ติดต่อ Gunicorn ไม่ได้

```bash
# ตรวจสอบว่า Gunicorn รันอยู่
sudo systemctl status smarttexttospeech

# ตรวจสอบ port 5000
ss -tlnp | grep 5000

# ดู error log
sudo journalctl -u smarttexttospeech -n 50
```

### "No audio received" error

edge-tts เชื่อมต่อ Microsoft server ไม่ได้

```bash
# ทดสอบอินเทอร์เน็ตของ server
curl -I https://speech.platform.bing.com

# ถ้า timeout — ตรวจสอบ firewall outbound rules
# Microsoft Edge TTS ใช้ HTTPS (port 443) ออกไปข้างนอก
sudo ufw status verbose
```

### Permission Denied ใน audio/ directory

```bash
sudo chown -R www-data:www-data /var/www/smarttexttospeech/audio
sudo chmod 775 /var/www/smarttexttospeech/audio
```

### Gunicorn timeout (ข้อความยาวมาก)

แก้ไขใน `gunicorn.conf.py`:

```python
timeout = 180   # เพิ่มจาก 120 เป็น 180 วินาที
```

แล้ว restart service:

```bash
sudo systemctl restart smarttexttospeech
```

### ดู Log แบบเต็ม

```bash
# Application log
sudo tail -100 /var/log/smarttexttospeech/error.log

# Nginx log
sudo tail -100 /var/log/nginx/smarttexttospeech-error.log

# systemd log
sudo journalctl -u smarttexttospeech --since "1 hour ago"
```

---

## สรุป Stack

```
Internet
    │
    ▼
┌─────────────────────┐
│  Nginx (port 80/443)│  ← Reverse proxy, SSL termination, static files
└──────────┬──────────┘
           │ proxy_pass http://127.0.0.1:5000
           ▼
┌─────────────────────┐
│  Gunicorn (port 5000)│  ← WSGI server, manages worker processes
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Flask (app.py)     │  ← Application logic
└──────────┬──────────┘
           │ HTTPS request
           ▼
┌─────────────────────┐
│  Microsoft Edge TTS │  ← Neural TTS API (ฟรี, ต้องการอินเทอร์เน็ต)
└─────────────────────┘
```
