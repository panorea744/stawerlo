import requests
import re
import urllib3
import warnings
import os

# --- AYARLAR ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}
TIMEOUT_VAL = 15
PROXY_URL = "https://seep.eu.org/"
OUTPUT_FOLDER = "olta"

# --- SABİT M3U8 BAŞLIĞI ---
M3U8_HEADER = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""

# --- KANAL ID HARİTASI (Dosya Adı: Selçuk ID) ---
SELCUK_NAMES = {
    "selcukobs1": "selcukobs1",
    "selcukbeinsports1": "selcukbeinsports1",
    "selcukbeinsports2": "selcukbeinsports2",
    "selcukbeinsports3": "selcukbeinsports3",
    "selcukbeinsports4": "selcukbeinsports4",
    "selcukbeinsports5": "selcukbeinsports5",
    "selcukbeinsportsmax1": "selcukbeinsportsmax1",
    "selcukbeinsportsmax2": "selcukbeinsportsmax2",
    "selcukssport1": "selcukssport",
    "selcukssport2": "selcukssport2",
    "selcuksmartspor1": "selcuksmartspor",
    "selcuksmartspor2": "selcuksmartspor2",
    "selcuktivibuspor1": "selcuktivibuspor1",
    "selcuktivibuspor2": "selcuktivibuspor2",
    "selcuktivibuspor3": "selcuktivibuspor3",
    "selcuktivibuspor4": "selcuktivibuspor4",
    "sssplus1": "sssplus1",
    "sssplus2": "sssplus2",
    "selcuktabiispor1": "selcuktabiispor1", 
    "selcuktabiispor2": "selcuktabiispor2", 
    "selcuktabiispor3": "selcuktabiispor3", 
    "selcuktabiispor4": "selcuktabiispor4", 
    "selcuktabiispor5": "selcuktabiispor5"
}

# --- YARDIMCI FONKSİYONLAR ---
def get_html_proxy(url):
    target_url = PROXY_URL + url
    try:
        r = requests.get(target_url, headers=HEADERS, timeout=TIMEOUT_VAL, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Proxy Hata: {e}")
        return None

def get_html_direct(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT_VAL, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Direkt Hata: {e}")
        return None

def find_base_url():
    print("--- Selçuk Sports Taranıyor ---")
    
    # 1. Ana sayfayı Proxy ile bul
    start_url = "https://www.selcuksportshd.is/"
    html = get_html_proxy(start_url)

    if not html:
        print("❌ Ana sayfaya ulaşılamadı.")
        return None

    # 2. Aktif domaini bul
    active_domain = ""
    # Mobil uyumlu linki arıyoruz genelde en günceli o oluyor
    section_match = re.search(r'data-device-mobile[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
    if section_match:
        link_match = re.search(r'href=["\'](https?://[^"\']*selcuksportshd[^"\']+)["\']', section_match.group(1))
        if link_match:
            active_domain = link_match.group(1).strip()
            if active_domain.endswith('/'): active_domain = active_domain[:-1]
    
    if not active_domain:
        print("❌ Aktif domain bulunamadı.")
        return None
    
    print(f"✅ Aktif Domain: {active_domain}")

    # 3. Domain sayfasına git (PROXY OLMADAN)
    domain_html = get_html_direct(active_domain)
    if not domain_html:
        return None

    # 4. Player linklerini bul
    player_links = re.findall(r'data-url=["\'](https?://[^"\']+?id=[^"\']+?)["\']', domain_html)
    if not player_links:
        player_links = re.findall(r'href=["\'](https?://[^"\']+?index\.php\?id=[^"\']+?)["\']', domain_html)
    
    if not player_links:
        print("❌ Player linkleri bulunamadı.")
        return None

    base_stream_url = ""

    # 5. Base URL'i çek
    for player_url in player_links:
        print(f"🔍 Player taranıyor: {player_url}")
        html_player = get_html_direct(player_url)
        if html_player:
            # Olası patternler
            patterns = [
                r'this\.baseStreamUrl\s*=\s*[\'"](https://[^\'"]+)[\'"]',
                r'const baseStreamUrl\s*=\s*[\'"](https://[^\'"]+)[\'"]',
                r'baseStreamUrl\s*:\s*[\'"](https://[^\'"]+)[\'"]',
                r'streamUrl\s*=\s*[\'"](https://[^\'"]+)[\'"]'
            ]
            for pattern in patterns:
                stream_match = re.search(pattern, html_player)
                if stream_match:
                    base_stream_url = stream_match.group(1)
                    # Live klasörünü kontrol et
                    if 'live/' in base_stream_url:
                        base_stream_url = base_stream_url.split('live/')[0] + 'live/'
                    print(f"🎯 Yayın URL Tabanı Bulundu: {base_stream_url}")
                    break
            if base_stream_url:
                break
    
    if not base_stream_url:
        print("❌ Yayın URL'si hiçbir playerda bulunamadı.")
        return None

    if not base_stream_url.endswith('/'):
        base_stream_url += '/'
    
    if 'live/' not in base_stream_url:
        base_stream_url = base_stream_url.rstrip('/') + '/live/'

    return base_stream_url

def main():
    # Klasör oluştur
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    # Base URL'i bul
    base_url = find_base_url()
    
    if not base_url:
        print("⚠️ Güncel link bulunamadığı için işlem iptal edildi.")
        return

    print(f"⚡ Linkler '{OUTPUT_FOLDER}' klasörüne yazılıyor...")
    
    count = 0
    # Kanalları oluştur ve kaydet
    for file_name, selcuk_id in SELCUK_NAMES.items():
        
        # URL Oluşturma Mantığı (Senin koddan alındı)
        if "sssplus" in selcuk_id:
            # S Sport Plus özel durumu
            if "1" in selcuk_id:
                stream_url = base_url + "sssplus1/playlist.m3u8"
            else:
                stream_url = base_url + "sssplus2/playlist.m3u8"
        elif selcuk_id in base_url:
            stream_url = base_url + "playlist.m3u8"
        else:
            stream_url = base_url + selcuk_id + "/playlist.m3u8"
        
        # Dosya İçeriği (Proxy yok, saf link)
        file_content = f"{M3U8_HEADER}\n{stream_url}"
        
        # Kaydet
        file_path = os.path.join(OUTPUT_FOLDER, f"{file_name}.m3u8")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)
        
        count += 1
        print(f"💾 {file_name}.m3u8 oluşturuldu.")

    print(f"\n✅ İŞLEM TAMAM! {count} adet güncel kanal kaydedildi.")

if __name__ == "__main__":
    main()
