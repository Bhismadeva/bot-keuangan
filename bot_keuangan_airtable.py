# === VERSI AIRTABLE TANPA GOOGLE CLOUD ===
# Gunakan Airtable sebagai pengganti Google Sheets. Gratis dan tidak butuh kartu kredit.

# === INSTALASI LIBRARY ===
# pip install python-telegram-bot==13.15 requests

# === FILE: bot_keuangan_airtable.py ===
import re
import datetime
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ============ KONFIGURASI ============
TELEGRAM_TOKEN = '8144593976:AAFUL4pkpCLG3Vvq6U5nerJUtKR3zV55bSE'
AIRTABLE_API_KEY = 'pata4Q1Xxvp7F2ZHo.10438386bf4524b5fe374df986fbee94c9d8d19be74bce3eb05b47b3d0888297'
BASE_ID = 'appCS8e67mFvHEUJg'
TABLE_PENGELUARAN = 'Pengeluaran'
TABLE_PEMASUKAN = 'Pemasukan'

HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

# ============ FUNGSI PEMBANTU ============
def konversi_uang(teks: str) -> int:
    teks = teks.lower().replace("rp", "").strip()
    if 'jt' in teks:
        return int(float(teks.replace('jt', '').replace(',', '.')) * 1_000_000)
    elif 'k' in teks:
        return int(float(teks.replace('k', '').replace(',', '.')) * 1_000)
    elif 'rb' in teks:
        return int(float(teks.replace('rb', '').replace(',', '.')) * 1_000)
    else:
        return int(teks.replace('.', '').replace(',', ''))

def proses_pesan(pesan: str):
    pesan = pesan.lower()
    kategori = ""
    if pesan.startswith("pengeluaran"):
        kategori = "pengeluaran"
        isi = pesan.replace("pengeluaran", "", 1).strip()
    elif pesan.startswith("pemasukan"):
        kategori = "pemasukan"
        isi = pesan.replace("pemasukan", "", 1).strip()
    else:
        return None

    match = re.match(r"(.+?)\s(\d+[.,]?\d*(jt|k|rb)?)", isi)
    if not match:
        return None

    deskripsi = match.group(1).strip().title()
    jumlah_rp = konversi_uang(match.group(2))
    waktu = datetime.datetime.now().strftime("%d %B %Y %H:%M")
    return kategori, waktu, deskripsi, jumlah_rp

def kirim_ke_airtable(kategori, waktu, deskripsi, jumlah):
    table = TABLE_PENGELUARAN if kategori == 'pengeluaran' else TABLE_PEMASUKAN
    url_base = f"https://api.airtable.com/v0/{BASE_ID}/{table}"

    # Ambil jumlah data yang sudah ada → untuk isi kolom No
    list_response = requests.get(url_base, headers=HEADERS)
    if list_response.status_code != 200:
        print("Error saat ambil data jumlah No:", list_response.text)
        return False

    existing_records = list_response.json().get('records', [])
    nomor = len(existing_records) + 1

    # Data untuk dikirim
    data = {
        "fields": {
            # "No": nomor,  ← HAPUS BARIS INI
            "Tanggal & Waktu": waktu,
            "Deskripsi": deskripsi,
            "Jumlah": jumlah
        }
    }

    post_response = requests.post(url_base, headers=HEADERS, json=data)
    print("Status:", post_response.status_code)
    print("Response:", post_response.text)

    return post_response.status_code in [200, 201]

# ============ HANDLER TELEGRAM ============
def handle_message(update: Update, context: CallbackContext):
    pesan = update.message.text
    hasil = proses_pesan(pesan)

    if not hasil:
        update.message.reply_text("❌ Format tidak dikenali. Contoh: pengeluaran makan siang 25k")
        return

    kategori, waktu, deskripsi, jumlah = hasil
    sukses = kirim_ke_airtable(kategori, waktu, deskripsi, jumlah)

    if sukses:
        update.message.reply_text(f"✅ {kategori.title()} '{deskripsi}' sebesar Rp {jumlah:,} dicatat!")
    else:
        update.message.reply_text("⚠️ Gagal mencatat data ke Airtable. Coba lagi nanti.")

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Halo! Kirim 'pengeluaran makan siang 25k' atau 'pemasukan gaji 1.5jt' untuk mencatat keuanganmu.")

# ============ JALANKAN BOT ============
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
