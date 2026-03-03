<div align="center">

# 💰 ProfitMeter UMKM

### AI-Powered Profit Analyzer untuk Bisnis Indonesia

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![GPT-4o](https://img.shields.io/badge/AI-GPT--4o-10a37f?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)]()

**Satu-satunya tool analisis profit yang punya benchmark data industri UMKM Indonesia — bukan sekadar chatbot.**

[Demo](#demo) · [Fitur](#fitur-utama) · [Instalasi](#instalasi) · [Cara Pakai](#cara-pakai)

</div>

---

## 🎯 Kenapa ProfitMeter, bukan ChatGPT?

| | ChatGPT | ProfitMeter UMKM |
|---|---|---|
| Benchmark vs industri sejenis | ❌ | ✅ Data BPS + Bank Indonesia |
| Deteksi anomali keuangan otomatis | ❌ | ✅ 4 jenis anomali |
| Export laporan PDF profesional | ❌ | ✅ Lengkap dengan AI insight |
| Chart visual interaktif | ❌ | ✅ Bar chart real-time |
| Konteks UMKM Indonesia | ❌ | ✅ 10 jenis industri lokal |
| Kalkulasi profit live saat input | ❌ | ✅ Update tiap keystroke |
| Bisa scan foto/PDF laporan | ❌ | ✅ Vision AI |

---

## ✨ Fitur Utama

### 📊 Analisis Profit Mendalam
- Kalkulasi margin bersih, margin kotor, dan health score (0–100)
- Breakdown pengeluaran per kategori: HPP, gaji, sewa, marketing, dll
- Live calculator — profit terhitung otomatis saat kamu input angka

### 🏆 Benchmark vs Industri
Data benchmark dari **BPS 2023 & Bank Indonesia** untuk 10 industri UMKM:
- Warung Makan / Rumah Makan
- Toko Retail / Minimarket Lokal
- Kafe / Coffee Shop
- Kuliner Online / Cloud Kitchen
- Fashion / Pakaian
- Toko Online / E-commerce
- Jasa / Freelance / Konsultan
- Salon / Barbershop
- Laundry
- Konveksi / Garmen

### ⚠️ Deteksi Anomali Otomatis
Sistem otomatis mendeteksi jika:
- HPP melebihi 120% rata-rata industri
- Beban gaji di atas 130% standar
- Sewa terlalu mahal (>150% benchmark)
- Marketing tidak efisien (>200% benchmark)

### 📄 Export Laporan PDF Profesional
Satu klik — laporan lengkap berisi:
- Health Score & status bisnis
- Tabel keuangan + breakdown
- Benchmark comparison table
- Rekomendasi strategis dari AI
- Quick wins & prediksi 3 bulan

### 🤖 Chat Konsultan AI
Tanya strategi profit, cara potong biaya, pricing optimal — AI menjawab dengan konteks bisnis kamu yang sudah dianalisis.

### 📷 Scan Dokumen
Upload foto nota, struk, atau laporan keuangan — AI langsung baca dan analisis otomatis.

---

## 🎨 UI/UX Highlights

- **Particle System** — 55 partikel melayang dengan koneksi node dinamis
- **Custom Cursor** — cursor + ring effect dengan lag animation
- **Counter Animation** — angka naik dari 0 saat hasil analisis muncul
- **Animated Bar Charts** — benchmark bars slide masuk dengan easing
- **Card Hover Glow** — setiap metric card punya warna glow sesuai status
- **Staggered Reveals** — cards muncul bergantian saat halaman load
- **Live Sidebar Stats** — revenue/cost/profit/margin update real-time

---

## 🚀 Instalasi

### Prerequisites
- Python 3.8+
- API Key LiteLLM (atau OpenAI)

### Setup

```bash
# 1. Clone repository
git clone https://github.com/username/profitumkm.git
cd profitumkm

# 2. Install dependencies
pip install -r requirements.txt

# 3. Buat file .env
echo "LITELLM_API_KEY=api-key-kamu" > .env

# 4. Jalankan server
python app.py
```

Buka browser: **http://localhost:5002**

### Windows (PowerShell)

```powershell
cd "C:\path\to\profitumkm"
pip install -r requirements.txt
python app.py
```

---

## 📦 Dependencies

```
flask>=3.0.0
requests>=2.31.0
python-dotenv>=1.0.0
reportlab>=4.0.0
```

---

## 📁 Struktur Project

```
profitumkm/
├── app.py                  # Flask server & API endpoints
├── requirements.txt
├── .env                    # API key (buat sendiri, jangan di-commit!)
├── data/
│   └── benchmark.json      # Data benchmark 10 industri UMKM Indonesia
└── templates/
    └── index.html          # Single-page dashboard (full animated)
```

---

## 🔌 API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `POST` | `/api/analyze` | Analisis data keuangan manual |
| `POST` | `/api/analyze-file` | Analisis dari gambar/PDF |
| `POST` | `/api/export-pdf` | Generate laporan PDF |
| `POST` | `/api/chat` | Chat dengan konsultan AI |

### Contoh Request `/api/analyze`

```json
{
  "nama_bisnis": "Warung Bu Sari",
  "industri_key": "warung_makan",
  "bulan": "Januari 2025",
  "revenue": 25000000,
  "hpp": 11000000,
  "gaji": 3000000,
  "sewa": 2000000,
  "marketing": 500000,
  "lain": 300000
}
```

---

## 📊 Cara Kerja Benchmark

Data benchmark diambil dari:
- **Badan Pusat Statistik (BPS) 2023** — data UMKM nasional
- **Bank Indonesia** — laporan sektor riil
- **Asosiasi industri** — margin operasional per sektor

Sistem membandingkan rasio biaya kamu dengan rata-rata industri dan menandai anomali jika melebihi threshold tertentu.

---

## 🖼️ Demo

> Tambahkan screenshot atau GIF demo di sini

```
Input data keuangan → AI Analisis → Dashboard + Benchmark + PDF
```

---

## 🤝 Kontribusi

Pull request sangat welcome! Untuk perubahan besar, buka issue dulu ya.

1. Fork repo ini
2. Buat branch baru (`git checkout -b fitur/nama-fitur`)
3. Commit perubahan (`git commit -m 'Tambah fitur X'`)
4. Push ke branch (`git push origin fitur/nama-fitur`)
5. Buka Pull Request

---

## 📝 License

[MIT](LICENSE) — bebas dipakai, dimodifikasi, dan didistribusikan.

---

<div align="center">

Dibuat dengan ☕ untuk UMKM Indonesia 🇮🇩

**[⬆ Kembali ke atas](#-profitmeter-umkm)**

</div>
