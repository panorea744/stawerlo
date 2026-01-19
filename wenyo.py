import requests
from bs4 import BeautifulSoup
import re
import os
import urllib3
import warnings

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

# TARAMA İÇİN GEREKLİLER
PROXY = "https://proxy.freecdn.workers.dev/?url="
START_SITE = "https://taraftariumizle.org"
OUTPUT_FOLDER = "Emu"

# KANAL LİSTESİ
CHANNELS = [
    "androstreamlivebiraz1", "androstreamlivebs1", "androstreamlivebs2", "androstreamlivebs3",
    "androstreamlivebs4", "androstreamlivebs5", "androstreamlivebsm1", "androstreamlivebsm2",
    "androstreamlivess1", "androstreamlivess2", "androstreamlivets", "androstreamlivets1",
    "androstreamlivets2", "androstreamlivets3", "androstreamlivets4", "androstreamlivesm1",
    "androstreamlivesm2", "androstreamlivees1", "androstreamlivees2", "androstreamlivetb",
    "androstreamlivetb1", "androstreamlivetb2", "androstreamlivetb3", "androstreamlivetb4",
    "androstreamlivetb5", "androstreamlivetb6", "androstreamlivetb7", "androstreamlivetb8",
    "androstreamliveexn", "androstreamliveexn1", "androstreamliveexn2", "androstreamliveexn3",
    "androstreamliveexn4", "androstreamliveexn5", "androstreamliveexn6", "androstreamliveexn7",
    "androstreamliveexn8"
]

def get_src(u, ref=None):
    try:
        current_headers = HEADERS.copy()
        if ref: current_headers['Referer'] = ref
        r = requests.get(PROXY + u, headers=current_headers, verify=False, timeout=20)
        return r.text if r.status_code == 200 else None
    except:
        return None

def extract_number(url):
    nums = re.findall(r'\d+', url)
    return int(nums[-1]) if nums else 0

def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    print("🔍 Domain tarama başlatıldı...")
    
    # 1. AMP linkini bul
    h1 = get_src(START_SITE)
    if not h1: return
    s = BeautifulSoup(h1, 'html.parser')
    lnk = s.find('link', rel='amphtml')
    if not lnk: return
    amp = lnk.get('href')

    # 2. Iframe linkini bul
    h2 = get_src(amp)
    if not h2: return
    m = re.search(r'\[src\]="appState\.currentIframe".*?src="(https?://[^"]+)"', h2, re.DOTALL)
    if not m: return
    ifr = m.group(1)

    # 3. BaseUrls listesini çek
    h3 = get_src(ifr, ref=amp)
    if not h3: return
    bm = re.search(r'baseUrls\s*=\s*\[(.*?)\]', h3, re.DOTALL)
    if not bm: return

    # URL'leri temizle ve listele
    cl = bm.group(1).replace('"', '').replace("'", "").replace("\n", "").replace("\r", "")
    srvs = [x.strip().rstrip('/') for x in cl.split(',') if x.strip().startswith("http")]
    
    if not srvs:
        print("❌ Domain bulunamadı.")
        return

    # 4. En büyük sayılı domaini seç
    active_domain = max(srvs, key=extract_number)
    print(f"✅ En güncel domain: {active_domain}")

    # 5. Emu klasörüne dosyaları yaz
    count = 0
    for cid in CHANNELS:
        # Link yapısını kur
        furl = f"{active_domain}/{cid}.m3u8" if "checklist" in active_domain else f"{active_domain}/checklist/{cid}.m3u8"
        furl = furl.replace("checklist//", "checklist/")
        
        # Dosya içeriği (PROXY YOK, direkt link)
        file_content = f"{M3U8_HEADER}\n{furl}"
        
        file_path = os.path.join(OUTPUT_FOLDER, f"{cid}.m3u8")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)
        count += 1

    print(f"🏁 Tamamlandı! {count} dosya güncellendi.")

if __name__ == "__main__":
    main()
