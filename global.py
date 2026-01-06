import requests
import re
import urllib3
import warnings
import os

# --- CONFIGURATION ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}
TIMEOUT_VAL = 15
PROXY_URL = "https://seep.eu.org/"
OUTPUT_FILENAME = "DeaTHLesS-Bot-iptv.m3u"
STATIC_LOGO = "https://i.hizliresim.com/8xzjgqv.jpg"

# --- 1. SELCUK SPORTS LOGIC ---
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

def get_selcuk_content():
    print("--- 📡 Scanning Selcuk Sports ---")
    results = []
    
    def get_html_proxy(url):
        target_url = PROXY_URL + url
        try:
            r = requests.get(target_url, headers=HEADERS, timeout=TIMEOUT_VAL, verify=False)
            r.raise_for_status()
            return r.text
        except:
            return None

    def get_html_direct(url):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT_VAL, verify=False)
            r.raise_for_status()
            return r.text
        except:
            return None

    start_url = "https://www.selcuksportshd.is/"
    html = get_html_proxy(start_url)
    
    if not html:
        print("❌ Selcuk: Main page unreachable.")
        return results

    active_domain = ""
    section_match = re.search(r'data-device-mobile[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
    if section_match:
        link_match = re.search(r'href=["\'](https?://[^"\']*selcuksportshd[^"\']+)["\']', section_match.group(1))
        if link_match:
            active_domain = link_match.group(1).strip().rstrip('/')

    if not active_domain:
        print("❌ Selcuk: Active domain not found.")
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
            entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO}" group-title="Selçuk-Panel", {name}\n{link}'
            results.append(entry)
    else:
        print("❌ Selcuk: Stream URL not found.")

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
    print("--- 📡 Scanning Atom Spor ---")
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

# --- 3. TRGOALS LOGIC ---
TRGOALS_IDS = {
    "yayinzirve":"beIN Sports 1","yayininat":"beIN Sports 1","yayin1":"beIN Sports 1",
    "yayinb2":"beIN Sports 2","yayinb3":"beIN Sports 3","yayinb4":"beIN Sports 4",
    "yayinb5":"beIN Sports 5","yayinbm1":"beIN Sports Max 1","yayinbm2":"beIN Sports Max 2",
    "yayinss":"S Sport 1","yayinss2":"S Sport 2","yayint1":"Tivibu Spor 1",
    "yayint2":"Tivibu Spor 2","yayint3":"Tivibu Spor 3","yayint4":"Tivibu Spor 4",
    "yayinsmarts":"Smart Spor 1","yayinsms2":"Smart Spor 2","yayintrtspor":"TRT Spor",
    "yayintrtspor2":"TRT Spor 2","yayinas":"A Spor","yayinatv":"ATV",
    "yayintv8":"TV8","yayintv85":"TV8.5","yayinnbatv":"NBA TV",
    "yayinex1":"Tabii 1","yayinex2":"Tabii 2","yayinex3":"Tabii 3",
    "yayinex4":"Tabii 4","yayinex5":"Tabii 5","yayinex6":"Tabii 6",
    "yayinex7":"Tabii 7","yayinex8":"Tabii 8"
}

def get_trgoals_content():
    print("--- 📡 Scanning TRGoals ---")
    results = []
    base = "https://trgoals"
    domain = ""

    for i in range(1495, 2101):
        test = f"{base}{i}.xyz"
        try:
            r = requests.head(test, timeout=2)
            if r.status_code == 200:
                domain = test
                print(f"✅ TRGoals Domain: {domain}")
                break
        except:
            continue
            
    if not domain:
        print("❌ TRGoals: No domain found.")
        return results

    for cid, name in TRGOALS_IDS.items():
        try:
            url = f"{domain}/channel.html?id={cid}"
            r = requests.get(url, headers=HEADERS, timeout=5)
            match = re.search(r'const baseurl = "(.*?)"', r.text)
            if match:
                baseurl = match.group(1)
                full_url = f"{baseurl}{cid}.m3u8"
                entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO}" group-title="TRGoals-Panel", {name}\n#EXTVLCOPT:http-referer={domain}/\n{full_url}'
                results.append(entry)
        except:
            continue
    return results

# --- 4. ANDRO PANEL (STATIC) ---
def get_andro_content():
    print("--- 📡 Processing Andro Panel ---")
    results = []
    
    # Raw data mapped to proper names for standardization
    andro_data = [
        ("TR:beIN Sport 1 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivebiraz1.m3u8"),
        ("TR:beIN Sport 1 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivebs1.m3u8"),
        ("TR:beIN Sport 2 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivebs2.m3u8"),
        ("TR:beIN Sport 3 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivebs3.m3u8"),
        ("TR:beIN Sport 4 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivebs4.m3u8"),
        ("TR:beIN Sport 5 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivebs5.m3u8"),
        ("TR:beIN Sport Max 1 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivebsm1.m3u8"),
        ("TR:beIN Sport Max 2 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivebsm2.m3u8"),
        ("TR:S Sport 1 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivess1.m3u8"),
        ("TR:S Sport 2 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivess2.m3u8"),
        ("TR:Tivibu Sport HD", "https://bot-sport.aykara463.workers.dev/androstreamlivets.m3u8"),
        ("TR:Tivibu Sport 1 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivets1.m3u8"),
        ("TR:Tivibu Sport 2 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivets2.m3u8"),
        ("TR:Tivibu Sport 3 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivets3.m3u8"),
        ("TR:Tivibu Sport 4 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivets4.m3u8"),
        ("TR:Smart Sport 1 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivesm1.m3u8"),
        ("TR:Smart Sport 2 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivesm2.m3u8"),
        ("TR:Euro Sport 1 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivees1.m3u8"),
        ("TR:Euro Sport 2 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivees2.m3u8"),
        ("TR:Tabii HD", "https://bot-sport.aykara463.workers.dev/androstreamlivetb.m3u8"),
        ("TR:Tabii 1 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivetb1.m3u8"),
        ("TR:Tabii 2 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivetb2.m3u8"),
        ("TR:Tabii 3 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivetb3.m3u8"),
        ("TR:Tabii 4 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivetb4.m3u8"),
        ("TR:Tabii 5 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivetb5.m3u8"),
        ("TR:Tabii 6 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivetb6.m3u8"),
        ("TR:Tabii 7 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivetb7.m3u8"),
        ("TR:Tabii 8 HD", "https://bot-sport.aykara463.workers.dev/androstreamlivetb8.m3u8"),
        ("TR:Exxen HD", "https://bot-sport.aykara463.workers.dev/androstreamliveexn.m3u8"),
        ("TR:Exxen 1 HD", "https://bot-sport.aykara463.workers.dev/androstreamliveexn1.m3u8"),
        ("TR:Exxen 2 HD", "https://bot-sport.aykara463.workers.dev/androstreamliveexn2.m3u8"),
        ("TR:Exxen 3 HD", "https://bot-sport.aykara463.workers.dev/androstreamliveexn3.m3u8"),
        ("TR:Exxen 4 HD", "https://bot-sport.aykara463.workers.dev/androstreamliveexn4.m3u8"),
        ("TR:Exxen 5 HD", "https://bot-sport.aykara463.workers.dev/androstreamliveexn5.m3u8"),
        ("TR:Exxen 6 HD", "https://bot-sport.aykara463.workers.dev/androstreamliveexn6.m3u8"),
        ("TR:Exxen 7 HD", "https://bot-sport.aykara463.workers.dev/androstreamliveexn7.m3u8"),
        ("TR:Exxen 8 HD", "https://bot-sport.aykara463.workers.dev/androstreamliveexn8.m3u8")
    ]
    
    for name, url in andro_data:
        entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO}" group-title="Andro-Panel", {name}\n{url}'
        results.append(entry)
        
    return results

# --- MAIN EXECUTION ---
def main():
    print("🚀 Starting Multi-Source IPTV Generator...")
    
    all_content = ["#EXTM3U"]
    
    # 1. Get Selçuk
    selcuk_lines = get_selcuk_content()
    all_content.extend(selcuk_lines)
    
    # 2. Get Atom
    atom_lines = get_atom_content()
    all_content.extend(atom_lines)
    
    # 3. Get TRGoals
    trgoals_lines = get_trgoals_content()
    all_content.extend(trgoals_lines)
    
    # 4. Get Andro (Static)
    andro_lines = get_andro_content()
    all_content.extend(andro_lines)
    
    # Write to file
    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write("\n".join(all_content))
            
        full_path = os.path.abspath(OUTPUT_FILENAME)
        total_channels = len(all_content) - 1
        
        print(f"\n✅ SUCCESS: All sources merged!")
        print(f"💾 File: {OUTPUT_FILENAME}")
        print(f"📝 Total Channels: {total_channels}")
        print(f"📍 Path: {full_path}")
        
    except IOError as e:
        print(f"\n❌ File write error: {e}")

if __name__ == "__main__":
    main()
