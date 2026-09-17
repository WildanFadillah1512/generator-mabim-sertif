import time
import re
import qrcode
import fitz  # PyMuPDF
from playwright.sync_api import sync_playwright

def search_certificate(target_name, start_id, max_attempts=50):
    """
    Mencari sertifikat berdasarkan nama dengan iterasi nomor.
    """
    target_name_lower = target_name.lower().strip()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        for i in range(max_attempts):
            current_id = start_id + i
            cert_number = f"P/{current_id}/MABIM/IX/2023"
            print(f"[*] Mencoba nomor surat: {cert_number}")
            
            try:
                page.goto("https://certificate.nusaputra.ac.id/verify", wait_until="domcontentloaded", timeout=15000)
                
                # Mengisi form menggunakan locator paling umum untuk input teks
                input_locator = page.locator("input[type='text']")
                if input_locator.count() == 0:
                    input_locator = page.locator("input")
                
                input_locator.first.fill(cert_number)
                page.keyboard.press("Enter")
                
                # Cukup beri jeda 3 detik untuk AJAX selesai memuat, hindari networkidle yang bisa stuck
                page.wait_for_timeout(3000)
                
                # Ambil teks dan html untuk mencari uuid
                page_text = page.inner_text("body").lower()
                page_html = page.content()
                
                if target_name_lower in page_text:
                    # Cari UUID dengan regex dari HTML
                    uuid_match = re.search(r'api/v1/credentials/([a-f0-9\-]{36})', page_html)
                    if not uuid_match:
                        # Coba pola lain jika ada
                        uuid_match = re.search(r'uuid&quot;:&quot;([a-f0-9\-]{36})&quot;', page_html)
                        
                    if uuid_match:
                        uuid = uuid_match.group(1)
                        print(f"[+] COCOK! Nama '{target_name}' ditemukan pada nomor {cert_number}")
                        print(f"    UUID: {uuid}")
                        browser.close()
                        return cert_number, uuid
                    else:
                        print(f"[!] Nama cocok, tapi gagal mengekstrak UUID dari halaman.")
                else:
                    print(f"[-] Sertifikat tidak ditemukan untuk nomor ini.")
                    
            except Exception as e:
                print(f"[!] Error saat mengecek {cert_number}: {e}")
                
        browser.close()
    return None, None

def generate_qr(uuid, filename="temp_qr.png"):
    url = f"https://certificate.nusaputra.ac.id/verify/{uuid}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    return filename

def modify_pdf(template_path, output_path, new_name, new_cert_number, qr_path):
    print(f"[*] Memproses PDF template: {template_path}")
    doc = fitz.open(template_path)
    page = doc[0]
    
    # 1. Cari dan hapus teks nama lama (berusaha mencari "WARDAN NUGRAHA AHMAD")
    name_rects = page.search_for("WARDAN NUGRAHA AHMAD")
    if not name_rects:
        print("[!] Peringatan: Teks nama lama tidak ditemukan dengan tepat. Mencoba mencari 'WARDAN'")
        name_rects = page.search_for("WARDAN")
        
    for rect in name_rects:
        # Tambahkan ruang sedikit di kanan kiri rect untuk memastikan bersih, 
        # jangan terlalu lebar agar tidak memotong desain background di sebelah kanan
        rect.x0 -= 15
        rect.x1 += 15 
        page.add_redact_annot(rect, fill=(1, 1, 1))
    
    # 2. Cari dan hapus teks nomor sertifikat lama
    words = page.get_text("words")
    cert_x = 450
    cert_y = 700
    for w in words:
        if w[4].startswith("P/") and "MABIM" in w[4]:
            rect = fitz.Rect(w[0], w[1], w[2], w[3])
            # Perlebar redaction box secukupnya
            rect.x0 -= 10
            rect.x1 += 10
            page.add_redact_annot(rect, fill=(1, 1, 1))
            cert_x = w[0]
            cert_y = w[3]
    
    page.apply_redactions()
    
    # 3. Tulis teks nama baru menggunakan insert_text (lebih aman dari insert_textbox)
    page_width = page.rect.width
    
    # Font name 'ti-bo' adalah Times-Bold bawaan PyMuPDF, cocok untuk nama
    font_size_name = 37
    max_text_width = 450 # Batas area sangat aman agar tidak mengenai tangan maskot di x~190
    
    text_length = fitz.get_text_length(new_name.upper(), fontname="times-bold", fontsize=font_size_name)
    
    # Jika teks terlalu panjang, perkecil font-nya sampai muat
    while text_length > max_text_width and font_size_name > 15:
        font_size_name -= 1
        text_length = fitz.get_text_length(new_name.upper(), fontname="times-bold", fontsize=font_size_name)
        
    x_pos_name = (page_width - text_length) / 2
    
    if name_rects:
        # Sedikit diangkat agar sama persis baseline-nya
        y_pos_name = name_rects[0].y1 - 2 
    else:
        y_pos_name = 380 # Default perkiraan
        
    page.insert_text(
        fitz.Point(x_pos_name, y_pos_name), 
        new_name.upper(), 
        fontsize=font_size_name, 
        fontname="times-bold", 
        color=(0, 0, 0)
    )

    # 4. Tulis nomor sertifikat baru
    font_size_cert = 14.5
    cert_length = fitz.get_text_length(new_cert_number, fontname="helvetica-bold", fontsize=font_size_cert)
    
    # Berdasarkan posisi asli di PDF, X sekitar 35.0
    x_pos_cert = 35.0
    y_pos_cert = 505.0 # Default jika tidak ketemu
    
    # Dari bounding box aslinya: cert_y adalah y1 dari kata lama
    if cert_y:
        y_pos_cert = cert_y
        x_pos_cert = cert_x # Gunakan X asli agar rata kiri sempurna
        
    page.insert_text(
        fitz.Point(x_pos_cert, y_pos_cert), 
        new_cert_number, 
        fontsize=font_size_cert, 
        fontname="helvetica-bold", 
        color=(0, 0, 0)
    )
    
    # 5. Timpa QR Code Lama
    # Bbox QR Code lama: Rect(52.5, 391.1, 127.5, 466.1)
    qr_rect = fitz.Rect(52.5, 391.1, 127.5, 466.1)
    page.draw_rect(qr_rect, color=(1,1,1), fill=(1,1,1))
    
    if qr_path:
        page.insert_image(qr_rect, filename=qr_path)
    
    doc.save(output_path)
    print(f"[+] Selesai! PDF disimpan di: {output_path}")

if __name__ == "__main__":
    print("=== GENERATOR SERTIFIKAT MABIM ===")
    target_name = input("Masukkan Nama yang dicari: ").strip()
    start_id_str = input("Masukkan Nomor Awal pencarian (contoh: 2180): ").strip()
    
    try:
        start_id = int(start_id_str)
    except ValueError:
        print("Nomor Awal harus berupa angka!")
        exit(1)
        
    print(f"\n[1] Memulai Pencarian di Website untuk nama: {target_name}")
    found_cert_num, uuid = search_certificate(target_name, start_id, max_attempts=100)
    
    if found_cert_num:
        qr_filename = None
        if uuid and uuid != "UNKNOWN":
            print("\n[2] Membuat Barcode/QR Code baru...")
            qr_filename = "temp_qr.png"
            generate_qr(uuid, qr_filename)
        else:
            print("\n[2] Tidak dapat mengekstrak UUID yang valid dari halaman, melewati pembuatan QR Code.")
            
        print("\n[3] Memodifikasi Template PDF...")
        template_pdf = "Mabim wardan-nugraha-ahmad.pdf"
        output_pdf = f"Sertifikat_{target_name.replace(' ', '_')}.pdf"
        
        modify_pdf(template_pdf, output_pdf, target_name, found_cert_num, qr_filename)
    else:
        print("\n[-] Pencarian selesai. Nama tidak ditemukan dalam rentang pencarian.")
