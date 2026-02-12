# ZIVPN UDP Auto Tunnel + API & Telegram Manager

Proyek ini menyediakan skrip otomatis untuk menghubungkan server ke panel ZIVPN menggunakan OpenVPN UDP saja, melengkapi dengan service systemd supaya auto start/reconnect, menu terminal berwarna, HTTP API manager, dan bot Telegram untuk mengelola akun VPN langsung dari chat.

## Persyaratan
- Ubuntu 24.04 atau Debian 12
- Akses root (sudo)
- Data panel ZIVPN: domain/host, port UDP, license key, tanggal kedaluwarsa, URL API, token API (opsional)
- Token bot Telegram dan admin chat ID (opsional untuk fitur bot)

## Instalasi
### Metode Git Clone
```bash
sudo apt update -y && sudo apt install -y git
cd /opt
sudo git clone https://github.com/USER/REPO.git zivpn-udp
cd zivpn-udp
sudo chmod +x zivpn-udp.sh
sudo ./zivpn-udp.sh install
```

### Metode Unduh Langsung
```bash
wget -O zivpn-udp.sh https://raw.githubusercontent.com/USER/REPO/main/zivpn-udp.sh
wget -O telegram_bot.py https://raw.githubusercontent.com/USER/REPO/main/telegram_bot.py
wget -O LICENSE https://raw.githubusercontent.com/USER/REPO/main/LICENSE
chmod +x zivpn-udp.sh
sudo ./zivpn-udp.sh install
```

Setelah instalasi, jalankan menu interaktif dengan:
```bash
sudo ./zivpn-udp.sh
```

## Cara Kerja Utama
- Menghubungkan server ke ZIVPN sebagai client **UDP only** melalui OpenVPN.
- Membuat systemd service `/etc/systemd/system/zivpn-udp.service` agar tunnel otomatis berjalan dan reconnect.
- Menyimpan konfigurasi OVPN di `/etc/zivpn-udp/zivpn_udp.ovpn` dan konfigurasi JSON di `/etc/zivpn-udp/config.json`.
- Menyediakan sub-menu API untuk memanggil endpoint panel ZIVPN (/ping, /users, /add, /trial, /delete, /renew, /changepass, /backup, /restore).
- Menyediakan sub-menu Telegram Bot Manager untuk menyalin `telegram_bot.py` ke `/opt/zivpn-udp/`, membuat service `zivpn-bot`, dan mengelolanya.

## Menu Utama (ZIVPN UDP MANAGER)
- **Install / Setup Awal**: Pasang dependensi, buat OVPN UDP, simpan config JSON, dan buat service tunnel.
- **Start/Stop/Restart Tunnel**: Kontrol service `zivpn-udp`.
- **VPS Information**: Menampilkan info OS, kernel, CPU, RAM, dan disk.
- **Tunnel Logs**: Menampilkan log OpenVPN (`/var/log/zivpn-udp.log`).
- **Edit Config OVPN/JSON**: Membuka file konfigurasi untuk penyesuaian.
- **API Manager**: Sub-menu untuk panggilan HTTP API (ping, users, add, trial, delete, renew, changepass, backup, restore).
- **Telegram Bot Manager**: Sub-menu untuk setup bot, start/stop/status service bot.

## Bot Telegram
- Pastikan `telegram_bot_token` dan `telegram_admin_id` terisi di `/etc/zivpn-udp/config.json` atau isi melalui menu Telegram Bot Manager.
- Setup bot dari menu akan menyalin `telegram_bot.py` ke `/opt/zivpn-udp/` dan mengaktifkan service `zivpn-bot`.
- Instal dependensi bot:
```bash
pip install python-telegram-bot==20.7 requests
```
- Perintah yang didukung di Telegram:
  - `/start`, `/ping`, `/info`, `/users`, `/add user pass days`, `/trial minutes`, `/delete user`, `/renew user days`, `/changepass user pass`, `/backup`, `/restore id`.

## Troubleshooting
- **Tunnel tidak jalan**: cek `systemctl status zivpn-udp` dan lihat log `tail -n 50 /var/log/zivpn-udp.log`.
- **Bot tidak merespon**: cek `systemctl status zivpn-bot` dan pastikan token/admin ID sudah diisi.
- **API gagal**: pastikan `api_url` benar dan bisa diakses, serta token (jika ada) valid.
- **Konfigurasi**: ubah nilai di `/etc/zivpn-udp/config.json` lalu restart service terkait.
- 
