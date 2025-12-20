import requests
import re
import os
import warnings

# --- AYARLAR ---
warnings.filterwarnings('ignore')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/"
}

# --- SABİT M3U8 BAŞLIĞI ---
M3U8_HEADER = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""

# --- CORS PROXY LİNKİ ---
PROXY_PREFIX = "https://tools.odpch.ch/tmp/cors-proxy?url="

# --- KLASÖR ADI ---
OUTPUT_FOLDER = "Emu"

# --- KANAL ID LİSTESİ ---
CHANNEL_IDS = [
    "androstreamlivebiraz1",
    "androstreamlivebs1",
    "androstreamlivebs2",
    "androstreamlivebs3",
    "androstreamlivebs4",
    "androstreamlivebs5",
    "androstreamlivebsm1",
    "androstreamlivebsm2",
    "androstreamlivess1",
    "androstreamlivess2",
    "androstreamlivets1",
    "androstreamlivets2",
    "androstreamlivets3",
    "androstreamlivets4",
    "androstreamlivesm1",
    "androstreamlivesm2",
    "androstreamlivees1",
    "androstreamlivees2",
    "androstreamlivetb",
    "androstreamlivetb1",
    "androstreamlivetb2",
    "androstreamlivetb3",
    "androstreamlivetb4",
    "androstreamlivetb5",
    "androstreamlivetb6",
    "androstreamlivetb7",
    "androstreamlivetb8",
    "androstreamliveexn1",
    "androstreamliveexn2",
    "androstreamliveexn3",
    "androstreamliveexn4",
    "androstreamliveexn5",
    "androstreamliveexn6",
    "androstreamliveexn7",
    "androstreamliveexn8"
]

def main():
    # Klasör yoksa oluştur
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    print("--- Yayın Tarayıcı Başlatıldı ---")
    
    # 1. ADIM: Aktif Domaini Bul
    print("🔍 Aktif domain aranıyor (44-200)...")
    active_domain = None
    
    for i in range(44, 200):
        url = f"https://seep.eu.org/https://birazcikspor{i}.xyz/"
        try:
            response = requests.head(url, headers=HEADERS, timeout=2)
            if response.status_code == 200:
                active_domain = url
                print(f"✅ Aktif Domain: {active_domain}")
                break
        except:
            continue
    
    if not active_domain:
        print("❌ Domain bulunamadı. Çıkış yapılıyor.")
        return

    # 2. ADIM: Base URL Çek
    HEADERS['Referer'] = active_domain
    base_url = ""
    
    try:
        response = requests.get(active_domain, headers=HEADERS, timeout=10)
        id_match = re.search(r'event\.html\?id=([a-zA-Z0-9_]+)', response.text)
        found_id = id_match.group(1) if id_match else "androstreamlivebiraz1"
        
        event_url = f"{active_domain}event.html?id={found_id}"
        event_response = requests.get(event_url, headers=HEADERS, timeout=10)
        base_match = re.search(r'const\s+baseurls\s*=\s*\[\s*"([^"]+)"', event_response.text)
        
        if base_match:
            base_url = base_match.group(1)
            print(f"📡 Sunucu Linki Alındı: {base_url}")
        else:
            print("❌ Yayın sunucusu bulunamadı.")
            return

    except Exception as e:
        print(f"❌ Hata: {e}")
        return

    # 3. ADIM: Dosyaları Oluştur (Proxy Ekleyerek)
    print(f"⚡ Linkler dönüştürülüp '{OUTPUT_FOLDER}' klasörüne kaydediliyor...")
    
    count = 0
    for file_id in CHANNEL_IDS:
        raw_stream_url = f"{base_url}{file_id}.m3u8"
        final_url = f"{PROXY_PREFIX}{raw_stream_url}"
        
        file_content = f"{M3U8_HEADER}\n{final_url}"
        
        # Emu klasörüne kaydet
        file_path = os.path.join(OUTPUT_FOLDER, f"{file_id}.m3u8")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)
        
        count += 1
        print(f"💾 Kaydedildi: {file_id}.m3u8")

    print(f"\n✅ İŞLEM TAMAM! Toplam {count} dosya güncellendi.")

if __name__ == "__main__":
    main()
