import requests
import re
import urllib3
import warnings
import os

# --- YAPILANDIRMA ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}
# Dosya adını isteğine göre güncelledim
OUTPUT_FILENAME = "atom.m3u"
STATIC_LOGO = "https://i.hizliresim.com/8xzjgqv.jpg"

# --- ATOM SPOR LOGIC ---
ATOM_CHANNELS = [
    ("bein-sports-1", "beIN Sports 1"), ("bein-sports-2", "beIN Sports 2"),
    ("bein-sports-3", "beIN Sports 3"), ("bein-sports-4", "beIN Sports 4"),
    ("s-sport", "S Sport 1"), ("s-sport-2", "S Sport 2"),
    ("tivibu-spor-1", "Tivibu Spor 1"), ("tivibu-spor-2", "Tivibu Spor 2"),
    ("tivibu-spor-3", "Tivibu Spor 3"), ("trt-spor", "TRT Spor"),
    ("trt-yildiz", "TRT Yildiz"), ("trt1", "TRT 1"), ("aspor", "A Spor")
]

def get_atom_content():
    print("--- 📡 Atom Spor Taranıyor ---")
    results = []
    start_url = "https://url24.link/AtomSporTV"
    
    headers = HEADERS.copy()
    headers['Referer'] = 'https://url24.link/'

    base_domain = "https://www.atomsportv480.top"
    try:
        r = requests.get(start_url, headers=headers, allow_redirects=False, timeout=10)
        if 'location' in r.headers:
            loc = r.headers['location']
            r2 = requests.get(loc, headers=headers, allow_redirects=False, timeout=10)
            if 'location' in r2.headers:
                base_domain = r2.headers['location'].strip().rstrip('/')
                print(f"✅ Atom Domain: {base_domain}")
    except:
        pass

    for cid, name in ATOM_CHANNELS:
        try:
            matches_url = f"{base_domain}/matches?id={cid}"
            r = requests.get(matches_url, headers=headers, timeout=10)
            fetch_match = re.search(r'fetch\(\s*["\'](.*?)["\']', r.text)
            
            if fetch_match:
                fetch_url = fetch_match.group(1).strip()
                if not fetch_url.endswith(cid): fetch_url += cid
                
                cust_headers = headers.copy()
                cust_headers['Origin'] = base_domain
                cust_headers['Referer'] = base_domain
                
                r2 = requests.get(fetch_url, headers=cust_headers, timeout=10)
                m3u8_match = re.search(r'"(?:stream|url|source|deismackanal)":\s*"(.*?\.m3u8|.*?)"', r2.text)
                
                if m3u8_match:
                    link = m3u8_match.group(1).replace('\\', '')
                    if link.endswith('.m3u8'):
                        entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO}" group-title="Atom-Panel", {name}\n#EXTVLCOPT:http-referrer={base_domain}\n{link}'
                        results.append(entry)
                        print(f"Bulundu: {name}")
        except:
            continue
            
    return results

# --- MAIN EXECUTION ---
def main():
    print("🚀 Sadece Atom Spor Listesi Oluşturuluyor...")
    
    all_content = ["#EXTM3U"]
    
    # Sadece Atom fonksiyonunu çağırıyoruz
    atom_lines = get_atom_content()
    all_content.extend(atom_lines)
    
    # Dosyaya yazma işlemi
    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write("\n".join(all_content))
            
        full_path = os.path.abspath(OUTPUT_FILENAME)
        total_channels = len(all_content) - 1
        
        print(f"\n✅ İŞLEM TAMAMLANDI!")
        print(f"💾 Dosya Adı: {OUTPUT_FILENAME}")
        print(f"📝 Toplam Kanal: {total_channels}")
        print(f"📍 Kayıt Yeri: {full_path}")
        
    except IOError as e:
        print(f"\n❌ Dosya yazma hatası: {e}")

if __name__ == "__main__":
    main()
