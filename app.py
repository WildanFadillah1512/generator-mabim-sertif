import os
import time
import threading
import requests
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from generator_sertifikat import search_certificate, generate_qr, modify_pdf

app = Flask(__name__)
app.secret_key = 'super_secret_key_mabim'

# Pastikan folder output ada jika diperlukan
OUTPUT_DIR = "outputs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ping')
def ping():
    return "OK"

@app.route('/generate', methods=['POST'])
def generate():
    target_name = request.form.get('target_name', '').strip()
    start_id_str = request.form.get('start_id', '').strip()
    
    if not target_name or not start_id_str:
        flash("Semua kolom harus diisi!", "danger")
        return redirect(url_for('index'))
        
    try:
        start_id = int(start_id_str)
    except ValueError:
        flash("Nomor Awal harus berupa angka!", "danger")
        return redirect(url_for('index'))
        
    try:
        # 1. Cari Sertifikat
        found_cert_num, uuid = search_certificate(target_name, start_id, max_attempts=50)
        
        if not found_cert_num:
            flash(f"Sertifikat atas nama '{target_name}' tidak ditemukan setelah dicari dari {start_id}.", "warning")
            return redirect(url_for('index'))
            
        # 2. Buat QR Code
        qr_filename = None
        if uuid and uuid != "UNKNOWN":
            qr_filename = os.path.join(OUTPUT_DIR, f"qr_{uuid}.png")
            generate_qr(uuid, qr_filename)
            
        # 3. Modifikasi PDF
        template_pdf = "Mabim wardan-nugraha-ahmad.pdf"
        # Nama file output
        safe_name = target_name.replace(' ', '_').replace('/', '')
        output_pdf = os.path.join(OUTPUT_DIR, f"Sertifikat_{safe_name}.pdf")
        
        modify_pdf(template_pdf, output_pdf, target_name, found_cert_num, qr_filename)
        
        # Kirim file PDF ke user
        return send_file(output_pdf, as_attachment=True)
        
    except Exception as e:
        flash(f"Terjadi kesalahan internal: {str(e)}", "danger")
        return redirect(url_for('index'))

def keep_alive():
    """Ping URL sendiri setiap 5 menit agar Render tidak sleep"""
    url = "https://generator-mabim-sertif.onrender.com/ping"
    while True:
        try:
            time.sleep(300) # 5 menit
            requests.get(url)
            print(f"[Keep-Alive] Ping {url} berhasil.")
        except Exception as e:
            print(f"[Keep-Alive] Ping gagal: {e}")

# Jalankan thread keep-alive hanya saat server dijalankan
threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == '__main__':
    # Jalankan server
    app.run(host='0.0.0.0', port=5000, debug=False)
