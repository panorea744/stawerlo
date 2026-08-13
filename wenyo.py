import requests
import re
import os
import urllib3
import warnings
import concurrent.futures

# --- AYARLAR ---
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

# DOSYAYA YAZILACAK BAŞLIK
M3U8_HEADER = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""

OUTPUT_FOLDER = "Emu"

# İKİNCİ BOTTAKİ KANAL LİSTESİ
CHANNELS = [
    "androstreamlivebiraz1", "androstreamlivebs1", "androstreamlivebs2", "androstreamlivebs3",
    "androstreamlivebs4", "androstreamlivebs5", "androstreamlivebsm1", "androstreamlivebsm2",
    "androstreamlivess1", "androstreamlivess2", "androstreamlivets", "androstreamlivets1",
    "androstreamlivets2", "androstreamlivets3", "androstreamlivets4", "androstreamlivesm1",
    "androstreamlivesm2", "androstreamlivees1", "androstreamlivees2", "androstreamlivetb",
    "androstreamlivetb1", "androstreamlivetb2", "androstreamlivetb3", "androstreamlivetb4",
    "androstreamlivetb5", "androstreamlivetb6", "androstreamlivetb7", "androstreamlivetb8",
    "androstreamlivessplus1"
]

def check_domain(index):
    """Domainin aktif olup olmadığını kontrol eder."""
    url = f"https://mahsunsports{index}.xyz"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5, verify=False)
        if response.status_code == 200:
            return url
    except:
        return None
    return None

def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    print("🔍 Andro Panel için aktif domain aranıyor...")
    
    active_site = None
    # Daha hızlı bulması için aynı anda 20 istek atıyoruz. (İlerisi için aralığı 46-150 yaptım)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_domain, i) for i in range(46, 150)]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                active_site = result
                executor.shutdown(wait=False, cancel_futures=True)
                break

    if not active_site:
        print("❌ Aktif site bulunamadı.")
        return

    print(f"✅ Aktif Domain Bulundu: {active_site}")

    # Event sayfasından m3u8 baseurl'lerini çekme
    event_url = f"{active_site}/event.html?id=androstreamlivebs1"
    try:
        r2 = requests.get(event_url, headers=HEADERS, verify=False, timeout=10)
        h2_text = r2.text
    except Exception as e:
        print(f"❌ Event sayfası alınamadı. Hata: {e}")
        return

    # Baseurl listesini yakalama
    baseurl_match = re.search(r'baseurls\s*=\s*\[(.*?)\]', h2_text, re.DOTALL | re.IGNORECASE)
    if not baseurl_match:
        print("❌ baseurls bulunamadı.")
        return

    urls_text = baseurl_match.group(1).replace('"', '').replace("'", "").replace("\n", "").replace("\r", "")
    servers = [url.strip() for url in urls_text.split(',') if url.strip().startswith("http")]
    servers = list(set(servers))
    
    if not servers:
        print("❌ Sunucu listesi boş.")
        return

    print(f"📡 Bulunan Sunucular: {servers}")

    # Bulunan sunuculardan hangisinin aktif yayın verdiğini test et
    working_server = None
    test_id = "androstreamlivebs1"
    
    for server in servers:
        server = server.rstrip('/')
        test_url = f"{server}/{test_id}.m3u8" if "checklist" in server else f"{server}/checklist/{test_id}.m3u8"
        test_url = test_url.replace("checklist//", "checklist/")
        try:
            temp_response = requests.get(test_url, headers={'Referer': active_site + "/"}, verify=False, timeout=5)
            if temp_response.status_code == 200:
                working_server = server
                break
        except:
            continue

    if not working_server:
        print("❌ Çalışan sunucu bağlantısı bulunamadı.")
        return

    print(f"🔥 Aktif Sunucu Seçildi: {working_server}")

    # Kanalları Emu klasörüne yazdır
    count = 0
    working_server = working_server.rstrip('/')
    
    for cid in CHANNELS:
        # Link yapısını kur
        furl = f"{working_server}/{cid}.m3u8" if "checklist" in working_server else f"{working_server}/checklist/{cid}.m3u8"
        furl = furl.replace("checklist//", "checklist/")
        
        # Oynatıcılar için referer satırı ekleyelim (Yayınların kapanmaması için önemli)
        referer_line = f"#EXTVLCOPT:http-referrer={active_site}/"
        
        # Dosya içeriği (Proxy yok, Header ve Direkt Link)
        file_content = f"{M3U8_HEADER}\n{referer_line}\n{furl}"
        file_path = os.path.join(OUTPUT_FOLDER, f"{cid}.m3u8")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)
        count += 1

    print(f"🏁 Tamamlandı! {count} dosya '{OUTPUT_FOLDER}' klasörüne oluşturuldu.")

if __name__ == "__main__":
    main()
