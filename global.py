import requests
import re
import urllib3
import warnings
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# --- AYARLAR ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}
TIMEOUT_VAL = 15
PROXY_URL = "https://seep.eu.org/"
OUTPUT_FILENAME = "DeaTHLesS-Bot-iptv.m3u"
STATIC_LOGO = "https://i.hizliresim.com/8xzjgqv.jpg"

# --- 1. SELCUK SPORTS LOGIC (GÜNCELLENMİŞ REFERRER İLE) ---
SELCUK_NAMES = {
    "selcukbeinsports1": "beIN Sports 1",
    "selcukbeinsports2": "beIN Sports 2",
    "selcukbeinsports3": "beIN Sports 3",
    "selcukbeinsports4": "beIN Sports 4",
    "selcukbeinsports5": "beIN Sports 5",
    "selcukbeinsportsmax1": "beIN Sports Max 1",
    "selcukbeinsportsmax2": "beIN Sports Max 2",
    "selcukssport": "S Sport 1",
    "selcukssport2": "S Sport 2",
    "selcuksmartspor": "Smart Spor 1",
    "selcuksmartspor2": "Smart Spor 2",
    "selcuktivibuspor1": "Tivibu Spor 1",
    "selcuktivibuspor2": "Tivibu Spor 2",
    "selcuktivibuspor3": "Tivibu Spor 3",
    "selcuktivibuspor4": "Tivibu Spor 4",
    "sssplus1": "S Sport Plus 1",
    "sssplus2": "S Sport Plus 2",
    "selcuktabiispor1": "Tabii Spor 1",
    "selcuktabiispor2": "Tabii Spor 2",
    "selcuktabiispor3": "Tabii Spor 3",
    "selcuktabiispor4": "Tabii Spor 4",
    "selcuktabiispor5": "Tabii Spor 5"
}

SELCUK_REFERRER = "https://selcuksportshd1903.xyz"

def get_selcuk_content():
    print("--- 📡 Selçuk Sports Taranıyor ---")
    results = []
    
    def get_html_proxy(url):
        target_url = PROXY_URL + url
        try:
            r = requests.get(target_url, headers=HEADERS, timeout=TIMEOUT_VAL, verify=False)
            r.raise_for_status()
            return r.text
        except:
            return None

    def get_html_direct(url, referer=None):
        try:
            headers = HEADERS.copy()
            if referer:
                headers["Referer"] = referer
            r = requests.get(url, headers=headers, timeout=TIMEOUT_VAL, verify=False)
            r.raise_for_status()
            return r.text
        except:
            return None

    start_url = "https://www.selcuksportshd.is/"
    html = get_html_proxy(start_url)
    
    if not html:
        print("❌ Selcuk: Ana sayfaya ulaşılamadı.")
        return results

    active_domain = ""
    section_match = re.search(r'data-device-mobile[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
    if section_match:
        link_match = re.search(r'href=["\'](https?://[^"\']*selcuksportshd[^"\']+)["\']', section_match.group(1))
        if link_match:
            active_domain = link_match.group(1).strip().rstrip('/')

    if not active_domain:
        print("❌ Selcuk: Aktif domain bulunamadı.")
        return results

    print(f"✅ Selcuk Domain: {active_domain}")
    domain_html = get_html_direct(active_domain)
    
    if not domain_html:
        return results

    player_links = re.findall(r'data-url=["\'](https?://[^"\']+?id=[^"\']+?)["\']', domain_html)
    if not player_links:
        player_links = re.findall(r'href=["\'](https?://[^"\']+?index\.php\?id=[^"\']+?)["\']', domain_html)

    base_stream_url = ""
    patterns = [
        r'this\.baseStreamUrl\s*=\s*[\'"](https://[^\'"]+)[\'"]',
        r'const baseStreamUrl\s*=\s*[\'"](https://[^\'"]+)[\'"]',
        r'baseStreamUrl\s*:\s*[\'"](https://[^\'"]+)[\'"]',
        r'streamUrl\s*=\s*[\'"](https://[^\'"]+)[\'"]'
    ]

    for player_url in player_links:
        html_player = get_html_direct(player_url)
        if html_player:
            for pattern in patterns:
                stream_match = re.search(pattern, html_player)
                if stream_match:
                    base_stream_url = stream_match.group(1)
                    if 'live/' in base_stream_url:
                        base_stream_url = base_stream_url.split('live/')[0] + 'live/'
                    break
            if base_stream_url: break

    if base_stream_url:
        if not base_stream_url.endswith('/'): base_stream_url += '/'
        if 'live/' not in base_stream_url: base_stream_url = base_stream_url.rstrip('/') + '/live/'
        
        for cid, name in SELCUK_NAMES.items():
            link = f"{base_stream_url}{cid}/playlist.m3u8"
            entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO}" group-title="Selçuk-Panel", {name}\n#EXTVLCOPT:http-referrer={SELCUK_REFERRER}\n{link}'
            results.append(entry)
    else:
        print("❌ Selcuk: Stream URL bulunamadı.")

    return results

# --- 2. ATOM SPOR LOGIC ---
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
        except:
            continue
            
    return results

# --- 3. TRGOALS LOGIC (GÜNCELLENMİŞ - URL KISALTMA SERVİSİ İLE) ---
TRGOALS_IDS = {
    # BeIN Sports
    "yayinzirve": "beIN Sports 1",
    "yayin1": "beIN Sports 1",
    "yayininat": "beIN Sports 1",
    "yayinb2": "beIN Sports 2",
    "yayinb3": "beIN Sports 3",
    "yayinb4": "beIN Sports 4",
    "yayinb5": "beIN Sports 5",
    "yayinbm1": "beIN Sports Max 1",
    "yayinbm2": "beIN Sports Max 2",
    # S Sport
    "yayinss": "S Sport 1",
    "yayinss2": "S Sport 2",
    "yayinssplus": "S Sport Plus 1",
    "yayinssplus2": "S Sport Plus 2",
    # Tivibu
    "yayint1": "Tivibu Spor 1",
    "yayint2": "Tivibu Spor 2",
    "yayint3": "Tivibu Spor 3",
    "yayint4": "Tivibu Spor 4",
    # Smart Spor
    "yayinsmarts": "Smart Spor 1",
    "yayinsms2": "Smart Spor 2",
    # TRT & Ulusal
    "yayintrtspor": "TRT Spor",
    "yayintrtspor2": "TRT Spor 2",
    "yayinas": "A Spor",
    "yayinatv": "ATV",
    "yayintv8": "TV8",
    "yayintv85": "TV8.5",
    "yayinnbatv": "NBA TV",
    # Exxen (Avrupa Maçları)
    "yayinex1": "Exxen Spor 1",
    "yayinex2": "Exxen Spor 2",
    "yayinex3": "Exxen Spor 3",
    "yayinex4": "Exxen Spor 4",
    "yayinex5": "Exxen Spor 5",
    "yayinex6": "Exxen Spor 6",
    "yayinex7": "Exxen Spor 7",
    "yayinex8": "Exxen Spor 8",
    # Tabii (Konferans Ligi)
    "yayintabii1": "Tabii Spor 1",
    "yayintabii2": "Tabii Spor 2",
    "yayintabii3": "Tabii Spor 3",
    "yayintabii4": "Tabii Spor 4",
    "yayintabii5": "Tabii Spor 5"
}

def get_trgoals_content():
    print("--- 📡 TRGoals Taranıyor (URL Kısaltma ile) ---")
    results = []
    
    # URL kısaltma servisinden aktif domaini bul
    SHORT_URL = "https://raw.githack.com/eniyiyayinci/redirect-cdn/main/index.html"  # Bu senin dediğin link
    
    def follow_redirects(url):
        """URL yönlendirmelerini takip et"""
        try:
            headers = HEADERS.copy()
            # Twitter linki için özel header
            headers["User-Agent"] = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
            
            session = requests.Session()
            session.max_redirects = 5
            response = session.get(url, headers=headers, timeout=10, allow_redirects=True, verify=False)
            
            return response.url
        except:
            return None
    
    print("🔍 URL kısaltma servisinden aktif domain aranıyor...")
    
    # 1. Adım: Kısaltılmış URL'den aktif domaini bul
    final_url = follow_redirects(SHORT_URL)
    
    if not final_url:
        print("❌ URL kısaltma servisine ulaşılamadı, eski yönteme geçiliyor...")
        # Eski yöntemle domain bul
        base_pattern = "https://trgoals"
        for i in range(1511, 2101):
            test = f"{base_pattern}{i}.xyz"
            try:
                r = requests.get(test, headers=HEADERS, timeout=2, verify=False)
                if r.status_code == 200:
                    final_url = test
                    break
            except:
                continue
    
    if not final_url:
        print("❌ TRGoals: Aktif domain bulunamadı.")
        return results
    
    # Domaini temizle
    parsed = urlparse(final_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    
    print(f"✅ TRGoals Domain Bulundu: {domain}")
    
    # 2. Adım: VIEW-SOURCE Mantığı ile Kanalları Çek
    print("⏳ Kanallar çözümleniyor...")
    
    # Aktif domain için referer hazırla
    referer_url = domain + "/"
    
    success_count = 0
    for cid, name in TRGOALS_IDS.items():
        try:
            # Channel sayfasını al
            url = f"{domain}/channel.html?id={cid}"
            
            # Referer ile sayfa kaynağını al
            temp_headers = HEADERS.copy()
            temp_headers["Referer"] = referer_url
            
            r = requests.get(url, headers=temp_headers, timeout=5, verify=False)
            
            if r.status_code != 200:
                continue
                
            # CONFIG içinde baseUrl'i ara
            patterns = [
                r'CONFIG\s*=\s*{[^}]*baseUrl\s*:\s*["\'](.*?)["\']',
                r'baseUrl\s*:\s*["\'](.*?)["\']',
                r'const\s+BASE_URL\s*=\s*["\'](.*?)["\']',
                r'let\s+baseUrl\s*=\s*["\'](.*?)["\']',
                r'var\s+baseUrl\s*=\s*["\'](.*?)["\']',
                r'src\s*=\s*["\'](.*?\.m3u8)["\']'
            ]
            
            baseurl = ""
            for pattern in patterns:
                match = re.search(pattern, r.text, re.IGNORECASE)
                if match:
                    baseurl = match.group(1)
                    break
            
            if baseurl:
                # baseUrl temizleme
                baseurl = baseurl.rstrip('/')
                
                # URL oluştur
                if baseurl.endswith('.m3u8'):
                    full_url = baseurl
                else:
                    full_url = f"{baseurl}/{cid}.m3u8"
                
                # URL'yi kontrol et
                if not full_url.startswith(('http://', 'https://')):
                    # Eğer relative URL ise domain ekle
                    if full_url.startswith('/'):
                        full_url = domain + full_url
                    else:
                        full_url = domain + '/' + full_url
                
                # Referer bilgisini ekle
                entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO}" group-title="TRGoals-Panel", {name}\n#EXTVLCOPT:http-referer={referer_url}\n{full_url}'
                results.append(entry)
                success_count += 1
                print(f"✓ {name}: {cid} başarılı")
            else:
                # DEBUG için
                if r.text and len(r.text) > 100:
                    # Sayfada m3u8 ara
                    m3u8_match = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', r.text)
                    if m3u8_match:
                        full_url = m3u8_match.group(1)
                        entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO}" group-title="TRGoals-Panel", {name}\n#EXTVLCOPT:http-referer={referer_url}\n{full_url}'
                        results.append(entry)
                        success_count += 1
                        print(f"✓ {name}: M3U8 direkt bulundu")
                    
        except Exception as e:
            # Hata durumunda sessizce geç
            continue
            
    print(f"✅ TRGoals: {success_count} kanal bulundu.")
    return results

# --- 4. ANDRO PANEL (GÜNCELLENMİŞ VERSİYON) ---
def get_andro_content():
    print("--- 📡 Andro Panel Taranıyor ---")
    results = []
    
    PROXY = "https://proxy.freecdn.workers.dev/?url="
    START = "https://taraftariumizle.org"
    
    headers = HEADERS.copy()
    
    channels = [
        ("androstreamlivebiraz1", 'TR:beIN Sport 1 HD'),
        ("androstreamlivebs1", 'TR:beIN Sport 1 HD'),
        ("androstreamlivebs2", 'TR:beIN Sport 2 HD'),
        ("androstreamlivebs3", 'TR:beIN Sport 3 HD'),
        ("androstreamlivebs4", 'TR:beIN Sport 4 HD'),
        ("androstreamlivebs5", 'TR:beIN Sport 5 HD'),
        ("androstreamlivebsm1", 'TR:beIN Sport Max 1 HD'),
        ("androstreamlivebsm2", 'TR:beIN Sport Max 2 HD'),
        ("androstreamlivess1", 'TR:S Sport 1 HD'),
        ("androstreamlivess2", 'TR:S Sport 2 HD'),
        ("androstreamlivets", 'TR:Tivibu Sport HD'),
        ("androstreamlivets1", 'TR:Tivibu Sport 1 HD'),
        ("androstreamlivets2", 'TR:Tivibu Sport 2 HD'),
        ("androstreamlivets3", 'TR:Tivibu Sport 3 HD'),
        ("androstreamlivets4", 'TR:Tivibu Sport 4 HD'),
        ("androstreamlivesm1", 'TR:Smart Sport 1 HD'),
        ("androstreamlivesm2", 'TR:Smart Sport 2 HD'),
        ("androstreamlivees1", 'TR:Euro Sport 1 HD'),
        ("androstreamlivees2", 'TR:Euro Sport 2 HD'),
        ("androstreamlivetb", 'TR:Tabii HD'),
        ("androstreamlivetb1", 'TR:Tabii 1 HD'),
        ("androstreamlivetb2", 'TR:Tabii 2 HD'),
        ("androstreamlivetb3", 'TR:Tabii 3 HD'),
        ("androstreamlivetb4", 'TR:Tabii 4 HD'),
        ("androstreamlivetb5", 'TR:Tabii 5 HD'),
        ("androstreamlivetb6", 'TR:Tabii 6 HD'),
        ("androstreamlivetb7", 'TR:Tabii 7 HD'),
        ("androstreamlivetb8", 'TR:Tabii 8 HD'),
        ("androstreamliveexn", 'TR:Exxen HD'),
        ("androstreamliveexn1", 'TR:Exxen 1 HD'),
        ("androstreamliveexn2", 'TR:Exxen 2 HD'),
        ("androstreamliveexn3", 'TR:Exxen 3 HD'),
        ("androstreamliveexn4", 'TR:Exxen 4 HD'),
        ("androstreamliveexn5", 'TR:Exxen 5 HD'),
        ("androstreamliveexn6", 'TR:Exxen 6 HD'),
        ("androstreamliveexn7", 'TR:Exxen 7 HD'),
        ("androstreamliveexn8", 'TR:Exxen 8 HD'),
    ]

    def get_src(url, referer=None):
        try:
            temp_headers = headers.copy()
            if referer:
                temp_headers['Referer'] = referer
            r = requests.get(PROXY + url, headers=temp_headers, verify=False, timeout=20)
            return r.text if r.status_code == 200 else None
        except:
            return None

    # 1. Adım: Ana sayfayı al
    h1 = get_src(START)
    if not h1:
        print("❌ Andro: Ana sayfa alınamadı")
        return results

    # 2. Adım: AMP linkini bul
    soup = BeautifulSoup(h1, 'html.parser')
    amp_link = soup.find('link', rel='amphtml')
    if not amp_link:
        print("❌ Andro: AMP linki bulunamadı")
        return results
    
    amp_url = amp_link.get('href')
    print(f"✅ Andro AMP URL: {amp_url}")

    # 3. Adım: AMP sayfasını al
    h2 = get_src(amp_url)
    if not h2:
        print("❌ Andro: AMP sayfası alınamadı")
        return results

    # 4. Adım: Iframe URL'sini bul
    iframe_match = re.search(r'\[src\]="appState\.currentIframe".*?src="(https?://[^"]+)"', h2, re.DOTALL)
    if not iframe_match:
        print("❌ Andro: Iframe URL bulunamadı")
        return results
    
    iframe_url = iframe_match.group(1)
    print(f"✅ Andro Iframe URL: {iframe_url}")

    # 5. Adım: Iframe içeriğini al
    h3 = get_src(iframe_url, referer=amp_url)
    if not h3:
        print("❌ Andro: Iframe içeriği alınamadı")
        return results

    # 6. Adım: Base URL'leri bul
    baseurl_match = re.search(r'baseUrls\s*=\s*\[(.*?)\]', h3, re.DOTALL)
    if not baseurl_match:
        print("❌ Andro: Base URL'ler bulunamadı")
        return results

    # 7. Adım: URL'leri temizle ve listele
    urls_text = baseurl_match.group(1).replace('"', '').replace("'", "").replace("\n", "").replace("\r", "")
    servers = [url.strip() for url in urls_text.split(',') if url.strip().startswith("http")]
    servers = list(set(servers))  # Benzersiz yap
    
    print(f"✅ Andro: {len(servers)} sunucu bulundu")
    
    # 8. Adım: Aktif sunucuları test et
    active_servers = []
    test_id = "androstreamlivebs1"
    
    for server in servers:
        server = server.rstrip('/')
        test_url = f"{server}/{test_id}.m3u8" if "checklist" in server else f"{server}/checklist/{test_id}.m3u8"
        test_url = test_url.replace("checklist//", "checklist/")
        
        try:
            temp_headers = headers.copy()
            temp_headers['Referer'] = iframe_url
            response = requests.get(PROXY + test_url, headers=temp_headers, verify=False, timeout=5)
            if response.status_code == 200:
                active_servers.append(server)
                print(f"✓ Aktif sunucu: {server}")
        except:
            continue
    
    # 9. Adım: Tüm kanalları aktif sunuculara ekle
    for server in active_servers:
        server = server.rstrip('/')
        for cid, cname in channels:
            final_url = f"{server}/{cid}.m3u8" if "checklist" in server else f"{server}/checklist/{cid}.m3u8"
            final_url = final_url.replace("checklist//", "checklist/")
            
            # Referer bilgisini ekle
            entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO}" group-title="Andro-Panel", {cname}\n#EXTVLCOPT:http-referrer={iframe_url}\n{final_url}'
            results.append(entry)
    
    print(f"✅ Andro: {len(results)} kanal eklendi")
    return results

# --- MAIN EXECUTION ---
def main():
    print("🚀 Çok Kaynaklı IPTV Oluşturucu Başlatılıyor...")
    print(f"📌 Sabit Referrer: {SELCUK_REFERRER}")
    
    all_content = ["#EXTM3U"]
    
    # 1. Get Selçuk (Referrer eklendi)
    selcuk_lines = get_selcuk_content()
    all_content.extend(selcuk_lines)
    print(f"✅ Selçuk: {len(selcuk_lines)} kanal")
    
    # 2. Get Atom
    atom_lines = get_atom_content()
    all_content.extend(atom_lines)
    print(f"✅ Atom: {len(atom_lines)} kanal")
    
    # 3. Get TRGoals (Updated with URL shortener)
    trgoals_lines = get_trgoals_content()
    all_content.extend(trgoals_lines)
    print(f"✅ TRGoals: {len(trgoals_lines)} kanal")
    
    # 4. Get Andro (Güncellenmiş)
    andro_lines = get_andro_content()
    all_content.extend(andro_lines)
    print(f"✅ Andro: {len(andro_lines)} kanal")
    
    # Write to file
    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write("\n".join(all_content))
            
        full_path = os.path.abspath(OUTPUT_FILENAME)
        total_channels = len(all_content) - 1
        
        print("\n" + "="*50)
        print(f"✅ İŞLEM BAŞARILI: Tüm kaynaklar birleştirildi!")
        print(f"💾 Dosya: {OUTPUT_FILENAME}")
        print(f"📊 Toplam Kanal: {total_channels}")
        print(f"📍 Yol: {full_path}")
        print("="*50)
        
    except IOError as e:
        print(f"\n❌ Dosya yazma hatası: {e}")

if __name__ == "__main__":
    main()
