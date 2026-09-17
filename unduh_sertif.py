from playwright.sync_api import sync_playwright

def download_certificate(url, output_filename):
    with sync_playwright() as p:
        # Menjalankan browser Chromium (Chrome) di latar belakang
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"Sedang mengakses: {url}")
        
        # Buka URL dan tunggu sampai halaman selesai dimuat sepenuhnya
        page.goto(url, wait_until="networkidle")
        
        # Menyimpan halaman sebagai PDF
        print("Sedang memproses PDF...")
        page.pdf(
            path=output_filename,
            format="A4",
            print_background=True,
            landscape=True # Mengubah ke mode landscape jika sertifikat melebar
        )
        
        print(f"Selesai! Sertifikat berhasil disimpan sebagai: {output_filename}")
        browser.close()

if __name__ == "__main__":
    # URL Sertifikat Anda
    url_sertifikat = "https://certificate.nusaputra.ac.id/verify/64c53ce1-5144-4f06-81c1-3fb31de8955b"
    nama_file = "Sertifikat_Mabim_Wildan.pdf"
    
    download_certificate(url_sertifikat, nama_file)