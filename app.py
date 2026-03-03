"""
ProfitMeter UMKM
================
AI Profit Analyzer khusus UMKM Indonesia dengan:
- Benchmark vs industri sejenis (data BPS/BI)
- Export laporan PDF profesional
- Chart visual interaktif
- Deteksi anomali keuangan
"""

from flask import Flask, render_template, request, jsonify, send_file
import os, json, base64, requests, io
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

API_BASE_URL  = "https://litellm.koboi2026.biz.id/v1"
CHAT_ENDPOINT = f"{API_BASE_URL}/chat/completions"
MODEL_NAME    = "gpt-4o"


def get_api_key():
    key = os.environ.get("LITELLM_API_KEY")
    if not key:
        raise Exception("LITELLM_API_KEY tidak ditemukan di .env")
    return key


def load_benchmark():
    path = os.path.join(os.path.dirname(__file__), "data", "benchmark.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def call_ai(messages, max_tokens=2500):
    resp = requests.post(
        CHAT_ENDPOINT,
        headers={"Authorization": f"Bearer {get_api_key()}", "Content-Type": "application/json"},
        json={"model": MODEL_NAME, "max_tokens": max_tokens, "messages": messages},
        timeout=60
    )
    if resp.status_code != 200:
        raise Exception(f"API Error {resp.status_code}: {resp.text[:300]}")
    return resp.json()["choices"][0]["message"]["content"]


def clean_json(raw):
    c = raw.strip()
    if c.startswith("```"):
        c = c.split("```")[1]
        if c.startswith("json"):
            c = c[4:]
    return c.strip()


# ── ROUTES ──────────────────────────────

@app.route("/")
def index():
    bm = load_benchmark()
    industri_list = {k: v["nama"] for k, v in bm["industri"].items()}
    return render_template("index.html", industri_list=industri_list)


# ── API: ANALISIS UTAMA ──────────────────

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    bm   = load_benchmark()

    # Ambil data benchmark industri yang dipilih
    industri_key = data.get("industri_key", "")
    bench        = bm["industri"].get(industri_key, {})

    revenue   = float(data.get("revenue", 0))
    hpp       = float(data.get("hpp", 0))
    gaji      = float(data.get("gaji", 0))
    sewa      = float(data.get("sewa", 0))
    marketing = float(data.get("marketing", 0))
    lain      = float(data.get("lain", 0))

    total_pengeluaran = hpp + gaji + sewa + marketing + lain
    profit_kotor      = revenue - hpp
    profit_bersih     = revenue - total_pengeluaran
    margin_bersih     = (profit_bersih / revenue * 100) if revenue > 0 else 0
    margin_kotor      = (profit_kotor  / revenue * 100) if revenue > 0 else 0

    # Hitung rasio vs benchmark
    bench_margin  = bench.get("margin_bersih_rata", 0)
    bench_baik    = bench.get("margin_bersih_baik", 0)
    bench_hpp     = bench.get("hpp_persen", 0)
    bench_gaji    = bench.get("rasio_gaji_revenue", 0)
    bench_sewa    = bench.get("rasio_sewa_revenue", 0)
    bench_mkt     = bench.get("rasio_marketing_revenue", 0)

    rasio_hpp     = (hpp       / revenue * 100) if revenue > 0 else 0
    rasio_gaji    = (gaji      / revenue * 100) if revenue > 0 else 0
    rasio_sewa    = (sewa      / revenue * 100) if revenue > 0 else 0
    rasio_mkt     = (marketing / revenue * 100) if revenue > 0 else 0

    # Deteksi anomali
    anomali = []
    if bench_hpp   > 0 and rasio_hpp  > bench_hpp   * 1.2:
        anomali.append({"tipe": "HPP Terlalu Tinggi",    "nilai": f"{rasio_hpp:.1f}%",  "benchmark": f"{bench_hpp:.1f}%",  "selisih": f"+{rasio_hpp - bench_hpp:.1f}%",   "severity": "kritis"})
    if bench_gaji  > 0 and rasio_gaji > bench_gaji  * 1.3:
        anomali.append({"tipe": "Gaji di Atas Wajar",    "nilai": f"{rasio_gaji:.1f}%", "benchmark": f"{bench_gaji:.1f}%", "selisih": f"+{rasio_gaji - bench_gaji:.1f}%", "severity": "perhatian"})
    if bench_sewa  > 0 and rasio_sewa > bench_sewa  * 1.5:
        anomali.append({"tipe": "Sewa Terlalu Mahal",    "nilai": f"{rasio_sewa:.1f}%", "benchmark": f"{bench_sewa:.1f}%", "selisih": f"+{rasio_sewa - bench_sewa:.1f}%", "severity": "perhatian"})
    if bench_mkt   > 0 and rasio_mkt  > bench_mkt   * 2.0:
        anomali.append({"tipe": "Marketing Tidak Efisien","nilai": f"{rasio_mkt:.1f}%",  "benchmark": f"{bench_mkt:.1f}%",  "selisih": f"+{rasio_mkt - bench_mkt:.1f}%",   "severity": "info"})
    if margin_bersih < 0:
        anomali.append({"tipe": "🚨 BISNIS MERUGI",       "nilai": f"{margin_bersih:.1f}%", "benchmark": f"{bench_margin:.1f}%", "selisih": f"{margin_bersih:.1f}%", "severity": "kritis"})

    # Skor kesehatan
    skor = 100
    if bench_margin > 0:
        ratio = margin_bersih / bench_margin
        skor  = min(100, max(0, int(ratio * 70 + 30)))
    if len(anomali) > 0: skor -= len(anomali) * 8
    skor = max(0, skor)

    # Benchmark comparison data untuk chart
    benchmark_chart = {
        "labels":    ["HPP", "Gaji", "Sewa", "Marketing"],
        "kamu":      [round(rasio_hpp,1), round(rasio_gaji,1), round(rasio_sewa,1), round(rasio_mkt,1)],
        "benchmark": [bench_hpp, bench_gaji, bench_sewa, bench_mkt]
    }

    # AI analisis
    system_prompt = """Kamu adalah konsultan bisnis UMKM Indonesia senior.
Berikan analisis mendalam dan rekomendasi KONKRET berbahasa Indonesia.

Balas HANYA JSON valid tanpa markdown:
{
  "ringkasan_ai": "1-2 kalimat assessment kondisi bisnis",
  "kekuatan": ["poin1", "poin2"],
  "masalah_utama": ["masalah1", "masalah2"],
  "rekomendasi": [
    {"prioritas": "Tinggi", "aksi": "aksi konkret", "dampak": "estimasi dampak profit", "cara": "langkah implementasi"}
  ],
  "pricing_advice": "saran spesifik tentang harga",
  "quick_wins": ["aksi cepat 1 minggu ini", "aksi cepat 2", "aksi cepat 3"],
  "prediksi_3bulan": number,
  "catatan_prediksi": "penjelasan prediksi"
}"""

    user_msg = f"""Analisis UMKM berikut:

Jenis: {data.get('nama_bisnis', '')} ({bench.get('nama','')})
Revenue: Rp {revenue:,.0f}
HPP: Rp {hpp:,.0f} ({rasio_hpp:.1f}% dari revenue, benchmark: {bench_hpp}%)
Gaji: Rp {gaji:,.0f} ({rasio_gaji:.1f}%, benchmark: {bench_gaji}%)
Sewa: Rp {sewa:,.0f} ({rasio_sewa:.1f}%, benchmark: {bench_sewa}%)
Marketing: Rp {marketing:,.0f} ({rasio_mkt:.1f}%, benchmark: {bench_mkt}%)
Profit Bersih: Rp {profit_bersih:,.0f} (margin {margin_bersih:.1f}%)
Margin rata-rata industri: {bench_margin}% (bagus: {bench_baik}%)
Anomali terdeteksi: {len(anomali)} item
Konteks: {data.get('konteks', '')}

Berikan analisis tajam dan rekomendasi yang sangat spesifik untuk UMKM ini."""

    try:
        raw    = call_ai([{"role":"system","content":system_prompt},{"role":"user","content":user_msg}])
        ai     = json.loads(clean_json(raw))
    except Exception as e:
        ai = {
            "ringkasan_ai": "Analisis berhasil. Perhatikan anomali yang terdeteksi.",
            "kekuatan": ["Data keuangan tersedia"], "masalah_utama": [],
            "rekomendasi": [], "pricing_advice": "-",
            "quick_wins": [], "prediksi_3bulan": profit_bersih * 3,
            "catatan_prediksi": "Estimasi berdasarkan data saat ini."
        }

    result = {
        "keuangan": {
            "revenue": revenue, "hpp": hpp, "gaji": gaji, "sewa": sewa,
            "marketing": marketing, "lain": lain,
            "total_pengeluaran": total_pengeluaran,
            "profit_kotor": profit_kotor, "profit_bersih": profit_bersih,
            "margin_bersih": round(margin_bersih, 1),
            "margin_kotor":  round(margin_kotor,  1),
        },
        "benchmark": {
            "nama_industri":   bench.get("nama", ""),
            "margin_rata":     bench_margin,
            "margin_baik":     bench_baik,
            "catatan":         bench.get("catatan", ""),
            "posisi":          "Di atas rata-rata" if margin_bersih >= bench_baik else ("Rata-rata" if margin_bersih >= bench_margin else "Di bawah rata-rata"),
            "selisih_margin":  round(margin_bersih - bench_margin, 1),
            "chart":           benchmark_chart,
        },
        "skor":    skor,
        "status":  "Sehat" if skor >= 70 else ("Perhatian" if skor >= 40 else "Kritis"),
        "anomali": anomali,
        "ai":      ai,
        "meta": {
            "nama_bisnis": data.get("nama_bisnis", ""),
            "tanggal":     datetime.now().strftime("%d %B %Y"),
            "bulan":       data.get("bulan", datetime.now().strftime("%B %Y")),
        }
    }

    return jsonify({"success": True, "data": result})


# ── API: EXPORT PDF ──────────────────────

@app.route("/api/export-pdf", methods=["POST"])
def export_pdf():
    """Generate laporan PDF profesional"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        return jsonify({"error": "reportlab tidak terinstall. Jalankan: pip install reportlab"}), 500

    data = request.get_json()
    d    = data.get("data", {})
    meta = d.get("meta", {})
    keu  = d.get("keuangan", {})
    bm   = d.get("benchmark", {})
    ai   = d.get("ai", {})
    ano  = d.get("anomali", [])

    # Warna brand
    C_DARK   = colors.HexColor("#0D1525")
    C_GREEN  = colors.HexColor("#00D4AA")
    C_RED    = colors.HexColor("#FF4D6D")
    C_GOLD   = colors.HexColor("#FFB800")
    C_GREY   = colors.HexColor("#6B7A99")
    C_LIGHT  = colors.HexColor("#F0F4FF")
    C_WHITE  = colors.white

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    story  = []

    def style(name, **kw):
        return ParagraphStyle(name, **kw)

    s_h1   = style("h1", fontName="Helvetica-Bold", fontSize=22, textColor=C_DARK, spaceAfter=4)
    s_h2   = style("h2", fontName="Helvetica-Bold", fontSize=13, textColor=C_DARK, spaceAfter=6)
    s_h3   = style("h3", fontName="Helvetica-Bold", fontSize=10, textColor=C_GREY, spaceAfter=4)
    s_body = style("body", fontName="Helvetica", fontSize=9, textColor=C_DARK, spaceAfter=4, leading=14)
    s_bold = style("bold", fontName="Helvetica-Bold", fontSize=9, textColor=C_DARK)
    s_cen  = style("cen", fontName="Helvetica", fontSize=9, textColor=C_GREY, alignment=TA_CENTER)
    s_grn  = style("grn", fontName="Helvetica-Bold", fontSize=9, textColor=C_GREEN)
    s_red  = style("red", fontName="Helvetica-Bold", fontSize=9, textColor=C_RED)

    def rp(v):
        if v is None: return "Rp -"
        v = float(v)
        if abs(v) >= 1e9:  return f"Rp {v/1e9:.1f}M"
        if abs(v) >= 1e6:  return f"Rp {v/1e6:.1f}jt"
        if abs(v) >= 1e3:  return f"Rp {v/1e3:.0f}rb"
        return f"Rp {v:,.0f}"

    def pct(v): return f"{float(v):.1f}%"

    # ── HEADER ──
    header_data = [[
        Paragraph(f"<b>LAPORAN ANALISIS PROFIT</b>", s_h1),
        Paragraph(f"<font color='#6B7A99' size='8'>{meta.get('nama_bisnis','')}<br/>{meta.get('bulan','')} · Dibuat {meta.get('tanggal','')}</font>", s_body)
    ]]
    t = Table(header_data, colWidths=[10*cm, 7*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_DARK),
        ('TEXTCOLOR',  (0,0), (-1,-1), C_WHITE),
        ('PADDING',    (0,0), (-1,-1), 16),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [C_DARK]),
        ('VALIGN',    (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # ── SKOR ──
    skor   = d.get("skor", 0)
    status = d.get("status", "-")
    s_col  = C_GREEN if skor >= 70 else (C_GOLD if skor >= 40 else C_RED)
    score_data = [[
        Paragraph(f"<b>HEALTH SCORE</b>", s_h3),
        Paragraph(f"<b>STATUS</b>", s_h3),
        Paragraph(f"<b>MARGIN BERSIH</b>", s_h3),
        Paragraph(f"<b>VS INDUSTRI</b>", s_h3),
    ],[
        Paragraph(f"<b><font size='20'>{skor}/100</font></b>", ParagraphStyle("sc", fontName="Helvetica-Bold", fontSize=20, textColor=s_col, alignment=TA_CENTER)),
        Paragraph(f"<b>{status}</b>", ParagraphStyle("st", fontName="Helvetica-Bold", fontSize=14, textColor=s_col, alignment=TA_CENTER)),
        Paragraph(f"<b>{pct(keu.get('margin_bersih',0))}</b>", ParagraphStyle("mb", fontName="Helvetica-Bold", fontSize=14, textColor=C_DARK, alignment=TA_CENTER)),
        Paragraph(f"<b>{bm.get('posisi','-')}</b>", ParagraphStyle("pos", fontName="Helvetica-Bold", fontSize=10, textColor=C_GREEN if 'atas' in bm.get('posisi','').lower() else C_RED, alignment=TA_CENTER)),
    ]]
    t = Table(score_data, colWidths=[4.25*cm]*4)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F0F4FF")),
        ('BACKGROUND', (0,1), (-1,1), C_WHITE),
        ('BOX',        (0,0), (-1,-1), 0.5, colors.HexColor("#E0E7FF")),
        ('INNERGRID',  (0,0), (-1,-1), 0.5, colors.HexColor("#E0E7FF")),
        ('PADDING',    (0,0), (-1,-1), 12),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # ── AI RINGKASAN ──
    if ai.get("ringkasan_ai"):
        story.append(Paragraph("💡 Analisis AI", s_h2))
        story.append(Paragraph(ai["ringkasan_ai"], s_body))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E0E7FF")))
        story.append(Spacer(1, 0.3*cm))

    # ── KEUANGAN ──
    story.append(Paragraph("📊 Laporan Keuangan", s_h2))
    keu_rows = [
        [Paragraph("<b>Item</b>", s_bold), Paragraph("<b>Nilai</b>", s_bold), Paragraph("<b>% Revenue</b>", s_bold)],
        ["Total Revenue",           rp(keu.get("revenue")),           "100%"],
        ["HPP / Modal Produksi",    rp(keu.get("hpp")),               pct(keu.get("hpp",0)/keu.get("revenue",1)*100) if keu.get("revenue") else "-"],
        ["Gaji Karyawan",           rp(keu.get("gaji")),              pct(keu.get("gaji",0)/keu.get("revenue",1)*100) if keu.get("revenue") else "-"],
        ["Sewa + Operasional",      rp(keu.get("sewa")),              pct(keu.get("sewa",0)/keu.get("revenue",1)*100) if keu.get("revenue") else "-"],
        ["Marketing",               rp(keu.get("marketing")),         pct(keu.get("marketing",0)/keu.get("revenue",1)*100) if keu.get("revenue") else "-"],
        ["Lain-lain",               rp(keu.get("lain")),              pct(keu.get("lain",0)/keu.get("revenue",1)*100) if keu.get("revenue") else "-"],
        [Paragraph("<b>Total Pengeluaran</b>", s_bold), Paragraph(f"<b>{rp(keu.get('total_pengeluaran'))}</b>", s_bold), ""],
        [Paragraph("<b>PROFIT BERSIH</b>", ParagraphStyle("pb", fontName="Helvetica-Bold", fontSize=10, textColor=C_GREEN if keu.get("profit_bersih",0)>=0 else C_RED)),
         Paragraph(f"<b>{rp(keu.get('profit_bersih'))}</b>", ParagraphStyle("pbv", fontName="Helvetica-Bold", fontSize=10, textColor=C_GREEN if keu.get("profit_bersih",0)>=0 else C_RED)),
         Paragraph(f"<b>{pct(keu.get('margin_bersih',0))}</b>", ParagraphStyle("pbp", fontName="Helvetica-Bold", fontSize=10, textColor=C_GREEN if keu.get("profit_bersih",0)>=0 else C_RED))],
    ]
    t = Table(keu_rows, colWidths=[8*cm, 5*cm, 4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,0), C_DARK),
        ('TEXTCOLOR',    (0,0), (-1,0), C_WHITE),
        ('BACKGROUND',   (0,-1),(-1,-1), colors.HexColor("#F0FFF8")),
        ('BACKGROUND',   (0,-2),(-1,-2), colors.HexColor("#F8F9FF")),
        ('INNERGRID',    (0,0), (-1,-1), 0.3, colors.HexColor("#E0E7FF")),
        ('BOX',          (0,0), (-1,-1), 0.5, colors.HexColor("#C7D2FE")),
        ('PADDING',      (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS',(0,1),(-1,-3), [C_WHITE, colors.HexColor("#FAFBFF")]),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # ── BENCHMARK ──
    story.append(Paragraph("🏆 Benchmark vs Industri", s_h2))
    story.append(Paragraph(f"Dibandingkan dengan rata-rata <b>{bm.get('nama_industri','')}</b>:", s_body))
    bm_rows = [
        [Paragraph("<b>Indikator</b>", s_bold), Paragraph("<b>Bisnis Kamu</b>", s_bold), Paragraph("<b>Rata-rata Industri</b>", s_bold), Paragraph("<b>Status</b>", s_bold)],
        ["Margin Bersih",
         pct(keu.get("margin_bersih",0)),
         pct(bm.get("margin_rata",0)),
         Paragraph("<b>✓ Bagus</b>" if keu.get("margin_bersih",0) >= bm.get("margin_rata",0) else "<b>↓ Perlu Naik</b>",
                   ParagraphStyle("bms", fontName="Helvetica-Bold", fontSize=9, textColor=C_GREEN if keu.get("margin_bersih",0) >= bm.get("margin_rata",0) else C_RED))],
    ]
    # tambah baris dari chart data
    bc = bm.get("chart", {})
    labels = bc.get("labels", [])
    kamu_v = bc.get("kamu", [])
    bench_v= bc.get("benchmark", [])
    for i, lbl in enumerate(labels):
        k = kamu_v[i] if i < len(kamu_v) else 0
        b = bench_v[i] if i < len(bench_v) else 0
        ok = k <= b * 1.1
        bm_rows.append([
            lbl, pct(k), pct(b),
            Paragraph("<b>✓ Efisien</b>" if ok else "<b>↑ Terlalu Tinggi</b>",
                ParagraphStyle("x", fontName="Helvetica-Bold", fontSize=9, textColor=C_GREEN if ok else C_RED))
        ])
    t = Table(bm_rows, colWidths=[5*cm, 4*cm, 4.5*cm, 3.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), C_DARK),
        ('TEXTCOLOR',     (0,0), (-1,0), C_WHITE),
        ('INNERGRID',     (0,0), (-1,-1), 0.3, colors.HexColor("#E0E7FF")),
        ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor("#C7D2FE")),
        ('PADDING',       (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [C_WHITE, colors.HexColor("#FAFBFF")]),
    ]))
    story.append(t)
    story.append(Paragraph(f"<font color='#6B7A99' size='8'>💡 {bm.get('catatan','')}</font>", s_body))
    story.append(Spacer(1, 0.5*cm))

    # ── ANOMALI ──
    if ano:
        story.append(Paragraph("⚠️ Anomali Terdeteksi", s_h2))
        for a in ano:
            sev_color = C_RED if a["severity"] == "kritis" else C_GOLD
            ano_row = [[
                Paragraph(f"<b>{a['tipe']}</b>", ParagraphStyle("at", fontName="Helvetica-Bold", fontSize=9, textColor=sev_color)),
                Paragraph(f"Kamu: <b>{a['nilai']}</b> | Benchmark: <b>{a['benchmark']}</b> | Selisih: <b>{a['selisih']}</b>", s_body),
            ]]
            t = Table(ano_row, colWidths=[5*cm, 12*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFF5F5") if a["severity"]=="kritis" else colors.HexColor("#FFFBEB")),
                ('BOX',        (0,0), (-1,-1), 0.5, sev_color),
                ('PADDING',    (0,0), (-1,-1), 8),
                ('LEFTPADDING',(0,0),(0,-1), 12),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.2*cm))
        story.append(Spacer(1, 0.3*cm))

    # ── REKOMENDASI ──
    rekom = ai.get("rekomendasi", [])
    if rekom:
        story.append(Paragraph("🎯 Rekomendasi Strategis", s_h2))
        for i, r in enumerate(rekom[:5], 1):
            p_col = C_RED if r.get("prioritas","")=="Tinggi" else (C_GOLD if r.get("prioritas","")=="Sedang" else colors.HexColor("#4D9FFF"))
            rows = [[
                Paragraph(f"<b>{i}. {r.get('aksi','')}</b>", s_bold),
                Paragraph(r.get("prioritas",""), ParagraphStyle("pr", fontName="Helvetica-Bold", fontSize=8, textColor=p_col)),
            ],[
                Paragraph(r.get("cara",""), s_body), ""
            ],[
                Paragraph(f"<font color='#00D4AA'>📈 Dampak: {r.get('dampak','')}</font>", s_body), ""
            ]]
            t = Table(rows, colWidths=[14*cm, 3*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), C_WHITE),
                ('BOX',        (0,0), (-1,-1), 0.5, colors.HexColor("#E0E7FF")),
                ('LEFTPADDING',(0,0),(-1,-1), 12),
                ('PADDING',    (0,0), (-1,-1), 6),
                ('SPAN',       (0,1), (-1,1)),
                ('SPAN',       (0,2), (-1,2)),
                ('TOPPADDING', (0,0), (-1,0), 10),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.2*cm))

    # ── QUICK WINS ──
    qw = ai.get("quick_wins", [])
    if qw:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("⚡ Quick Wins — Lakukan Minggu Ini", s_h2))
        for q in qw:
            story.append(Paragraph(f"✅  {q}", s_body))

    # ── PREDIKSI ──
    pred = ai.get("prediksi_3bulan")
    if pred:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("📈 Prediksi 3 Bulan", s_h2))
        story.append(Paragraph(f"Estimasi profit kumulatif 3 bulan: <b>{rp(pred)}</b>", s_body))
        if ai.get("catatan_prediksi"):
            story.append(Paragraph(ai["catatan_prediksi"], s_body))

    # ── FOOTER ──
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E0E7FF")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"<font color='#6B7A99' size='8'>Laporan dibuat oleh ProfitMeter UMKM · {meta.get('tanggal','')} · Data bersifat konfidensial</font>", s_cen))

    doc.build(story)
    buf.seek(0)

    nama = meta.get("nama_bisnis", "bisnis").replace(" ", "_")
    bulan = meta.get("bulan", "").replace(" ", "_")
    filename = f"Laporan_Profit_{nama}_{bulan}.pdf"

    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True, download_name=filename)


# ── API: CHAT ────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat():
    data    = request.get_json()
    history = data.get("history", [])
    pesan   = data.get("pesan", "")
    konteks = data.get("konteks", "")

    system = f"""Kamu adalah ProfitMeter AI, konsultan bisnis UMKM Indonesia.
Gaya: lugas, ramah, pakai Bahasa Indonesia, saran harus spesifik dan actionable.
Konteks bisnis: {konteks}
Selalu kaitkan jawaban dengan peningkatan profit nyata."""

    msgs = [{"role":"system","content":system}] + history[-10:] + [{"role":"user","content":pesan}]

    try:
        reply = call_ai(msgs, max_tokens=600)
        return jsonify({"success": True, "reply": reply})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 55)
    print("  💰 ProfitMeter UMKM — Server Berjalan!")
    print("  Buka browser: http://localhost:5002")
    print("=" * 55)
    app.run(debug=True, port=5002)
