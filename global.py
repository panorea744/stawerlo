import requests
import re
import urllib3
import warnings
import os
import concurrent.futures
import base64
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}
TIMEOUT_VAL = 15
PROXY_URL = "https://seep.eu.org/"
OUTPUT_FILENAME = "DeaTHLesS-Botiptv.m3u"
STATIC_LOGO = "https://i.hizliresim.com/8xzjgqv.jpg"

# ============================================
# 1. SELCUK SPORTS
# ============================================

SELCUK_NAMES = {
    "sbeinsports-1": "beIN Sports 1", "selcukobs1": "beIN Sports 1", "selcukbeinsports1": "beIN Sports 1",
    "selcukbeinsports2": "beIN Sports 2", "selcukbeinsports3": "beIN Sports 3",
    "selcukbeinsports4": "beIN Sports 4", "selcukbeinsports5": "beIN Sports 5",
    "selcukbeinsportsmax1": "beIN Sports Max 1", "selcukbeinsportsmax2": "beIN Sports Max 2",
    "selcukssport": "S Sport 1", "selcukssport2": "S Sport 2",
    "selcuksmartspor": "Smart Spor 1", "selcuksmartspor2": "Smart Spor 2",
    "selcuktivibuspor1": "Tivibu Spor 1", "selcuktivibuspor2": "Tivibu Spor 2",
    "selcuktivibuspor3": "Tivibu Spor 3", "selcuktivibuspor4": "Tivibu Spor 4",
    "sssplus1": "S Sport Plus 1", "sssplus2": "S Sport Plus 2",
    "selcuktabiispor1": "Tabii Spor 1", "selcuktabiispor2": "Tabii Spor 2",
    "selcuktabiispor3": "Tabii Spor 3", "selcuktabiispor4": "Tabii Spor 4",
    "selcuktabiispor5": "Tabii Spor 5"
}
SELCUK_REFERRER = "https://selcuksportshd1903.xyz"

def get_selcuk_content():
    print("--- 1. Selcuk Sports ---")
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
        return results

    active_domain = ""
    section_match = re.search(r'data-device-mobile[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
    if section_match:
        link_match = re.search(r'href=["\'](https?://[^"\']*selcuksportshd[^"\']+)["\']', section_match.group(1))
        if link_match:
            active_domain = link_match.group(1).strip().rstrip('/')

    if not active_domain:
        return results
    print(f"Selcuk Domain: {active_domain}")

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
            if base_stream_url:
                break

    if base_stream_url:
        if not base_stream_url.endswith('/'):
            base_stream_url += '/'
        if 'live/' not in base_stream_url:
            base_stream_url = base_stream_url.rstrip('/') + '/live/'

        for cid, name in SELCUK_NAMES.items():
            link = f"{base_stream_url}{cid}/playlist.m3u8"
            entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO}" group-title="Selçuk-Panel", {name}\n#EXTVLCOPT:http-referrer={SELCUK_REFERRER}\n{link}'
            results.append(entry)

    return results


# ============================================
# 2. ATOM SPOR
# ============================================

ATOM_CHANNELS = [
    ("bein-sports-1", "beIN Sports 1"), ("bein-sports-2", "beIN Sports 2"),
    ("bein-sports-3", "beIN Sports 3"), ("bein-sports-4", "beIN Sports 4"),
    ("s-sport", "S Sport 1"), ("s-sport-2", "S Sport 2"),
    ("tivibu-spor-1", "Tivibu Spor 1"), ("tivibu-spor-2", "Tivibu Spor 2"),
    ("tivibu-spor-3", "Tivibu Spor 3"), ("trt-spor", "TRT Spor"),
    ("trt-yildiz", "TRT Yildiz"), ("trt1", "TRT 1"), ("aspor", "A Spor")
]

def get_atom_content():
    print("--- 2. Atom Spor ---")
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
                print(f"Atom Domain: {base_domain}")
    except:
        pass

    for cid, name in ATOM_CHANNELS:
        try:
            matches_url = f"{base_domain}/matches?id={cid}"
            r = requests.get(matches_url, headers=headers, timeout=10)
            fetch_match = re.search(r'fetch\(\s*["\'](.*?)["\']', r.text)
            if fetch_match:
                fetch_url = fetch_match.group(1).strip()
                if not fetch_url.endswith(cid):
                    fetch_url += cid
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


# ============================================
# 3. TRGOALS
# ============================================

TRGOALS_STATIC_LIST = [
    ("TRGoals Ana", "https://spring-band-25c2.panorea1000.workers.dev/trgoals.m3u8"),
    ("beIN Sports 1 (Zirve)", "https://spring-band-25c2.panorea1000.workers.dev/zirve.m3u8"),
    ("beIN Sports 2", "https://spring-band-25c2.panorea1000.workers.dev/b2.m3u8"),
    ("beIN Sports 3", "https://spring-band-25c2.panorea1000.workers.dev/b3.m3u8"),
    ("beIN Sports 4", "https://spring-band-25c2.panorea1000.workers.dev/b4.m3u8"),
    ("beIN Sports 5", "https://spring-band-25c2.panorea1000.workers.dev/b5.m3u8"),
    ("beIN Sports Max 1", "https://spring-band-25c2.panorea1000.workers.dev/bm1.m3u8"),
    ("beIN Sports Max 2", "https://spring-band-25c2.panorea1000.workers.dev/bm2.m3u8"),
    ("S Sport 1", "https://spring-band-25c2.panorea1000.workers.dev/ss.m3u8"),
    ("S Sport 2", "https://spring-band-25c2.panorea1000.workers.dev/ss2.m3u8"),
    ("Smart Spor 1", "https://spring-band-25c2.panorea1000.workers.dev/smarts.m3u8"),
    ("Smart Spor 2", "https://spring-band-25c2.panorea1000.workers.dev/sms2.m3u8"),
    ("Tivibu Spor 1", "https://spring-band-25c2.panorea1000.workers.dev/t1.m3u8"),
    ("Tivibu Spor 2", "https://spring-band-25c2.panorea1000.workers.dev/t2.m3u8"),
    ("Tivibu Spor 3", "https://spring-band-25c2.panorea1000.workers.dev/t3.m3u8"),
    ("Tivibu Spor 4", "https://spring-band-25c2.panorea1000.workers.dev/t4.m3u8"),
    ("Eurosport 1", "https://spring-band-25c2.panorea1000.workers.dev/eu1.m3u8"),
    ("Eurosport 2", "https://spring-band-25c2.panorea1000.workers.dev/eu2.m3u8")
]

def get_trgoals_content():
    print("--- 3. TRGoals ---")
    results = []
    for name, url in TRGOALS_STATIC_LIST:
        entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO}" group-title="TRGoals-Panel", {name}\n{url}'
        results.append(entry)
    return results


# ============================================
# 4. ANDRO PANEL
# ============================================

def get_andro_content():
    print("--- 4. Andro Panel ---")
    results = []
    base_pattern = "https://mahsunsports{}.xyz"
    headers = HEADERS.copy()

    channels = [
        ("androstreamlivebiraz1", 'TR:beIN Sport 1 HD'), ("androstreamlivebs1", 'TR:beIN Sport 1 HD'),
        ("androstreamlivebs2", 'TR:beIN Sport 2 HD'), ("androstreamlivebs3", 'TR:beIN Sport 3 HD'),
        ("androstreamlivebs4", 'TR:beIN Sport 4 HD'), ("androstreamlivebs5", 'TR:beIN Sport 5 HD'),
        ("androstreamlivebsm1", 'TR:beIN Sport Max 1 HD'), ("androstreamlivebsm2", 'TR:beIN Sport Max 2 HD'),
        ("androstreamlivess1", 'TR:S Sport 1 HD'), ("androstreamlivess2", 'TR:S Sport 2 HD'),
        ("androstreamlivets", 'TR:Tivibu Sport HD'), ("androstreamlivets1", 'TR:Tivibu Sport 1 HD'),
        ("androstreamlivets2", 'TR:Tivibu Sport 2 HD'), ("androstreamlivets3", 'TR:Tivibu Sport 3 HD'),
        ("androstreamlivets4", 'TR:Tivibu Sport 4 HD'), ("androstreamlivesm1", 'TR:Smart Sport 1 HD'),
        ("androstreamlivesm2", 'TR:Smart Sport 2 HD'), ("androstreamlivees1", 'TR:Euro Sport 1 HD'),
        ("androstreamlivees2", 'TR:Euro Sport 2 HD'), ("androstreamliveexn", 'TR:Exxen HD'),
        ("androstreamliveexn1", 'TR:Exxen 1 HD'), ("androstreamliveexn2", 'TR:Exxen 2 HD'),
        ("androstreamliveexn3", 'TR:Exxen 3 HD'), ("androstreamliveexn4", 'TR:Exxen 4 HD'),
        ("androstreamliveexn5", 'TR:Exxen 5 HD'), ("androstreamliveexn6", 'TR:Exxen 6 HD'),
        ("androstreamliveexn7", 'TR:Exxen 7 HD'), ("androstreamliveexn8", 'TR:Exxen 8 HD')
    ]

    def check_domain(index):
        url = base_pattern.format(index)
        try:
            response = requests.get(url, headers=headers, timeout=5, verify=False)
            if response.status_code == 200:
                return url
        except:
            return None
        return None

    print("Andro Panel icin aktif domain araniyor (35-99)...")
    active_site = None

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_domain, i) for i in range(35, 100)]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                active_site = result
                executor.shutdown(wait=False, cancel_futures=True)
                break

    if not active_site:
        print("Andro Panel: Aktif site bulunamadi.")
        return results

    print(f"Andro Panel Domain: {active_site}")

    event_url = f"{active_site}/event.html?id=androstreamlivebs1"
    try:
        r2 = requests.get(event_url, headers=headers, verify=False, timeout=10)
        h2_text = r2.text
    except Exception as e:
        print(f"Andro Panel: Event sayfasi alinamadi. Hata: {e}")
        return results

    baseurl_match = re.search(r'baseurls\s*=\s*\[(.*?)\]', h2_text, re.DOTALL | re.IGNORECASE)
    if not baseurl_match:
        print("Andro Panel: baseurls bulunamadi.")
        return results

    urls_text = baseurl_match.group(1).replace('"', '').replace("'", "").replace("\n", "").replace("\r", "")
    servers = [url.strip() for url in urls_text.split(',') if url.strip().startswith("http")]
    servers = list(set(servers))
    print(f"Bulunan Sunucular: {servers}")

    active_servers = []
    test_id = "androstreamlivebs1"
    for server in servers:
        server = server.rstrip('/')
        test_url = f"{server}/{test_id}.m3u8" if "checklist" in server else f"{server}/checklist/{test_id}.m3u8"
        test_url = test_url.replace("checklist//", "checklist/")
        try:
            temp_response = requests.get(test_url, headers={'Referer': active_site + "/"}, verify=False, timeout=5)
            if temp_response.status_code == 200:
                active_servers.append(server)
        except:
            continue

    for server in active_servers:
        server = server.rstrip('/')
        for cid, cname in channels:
            final_url = f"{server}/{cid}.m3u8" if "checklist" in server else f"{server}/checklist/{cid}.m3u8"
            final_url = final_url.replace("checklist//", "checklist/")
            entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO}" group-title="Andro-Panel", {cname}\n#EXTVLCOPT:http-referrer={active_site}/\n{final_url}'
            results.append(entry)

    return results


# ============================================
# 5. XSPORT
# ============================================

def get_xsport_content():
    print("--- 5. XSport ---")
    results = []
    base_pattern = "https://www.xsportv{}.xyz/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    channel_ids = [
        "xbeinsports-1", "xbeinsports-2", "xbeinsports-3", "xbeinsports-4", "xbeinsports-5",
        "xbeinsportsmax-1", "xbeinsportsmax-2", "xtivibuspor-1", "xtivibuspor-2",
        "xtivibuspor-3", "xtivibuspor-4", "xssport", "xssport2", "xtabiispor1",
        "xtabiispor2", "xtabiispor3", "xtabiispor4", "xtabiispor5", "xtabiispor6", "xtabiispor7"
    ]

    def check_domain(index):
        url = base_pattern.format(index)
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return url
        except:
            return None

    def find_active_domain():
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(check_domain, i) for i in range(56, 1000)]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    executor.shutdown(wait=False, cancel_futures=True)
                    return result
        return None

    def get_stream_url(player_url, stream_id):
        try:
            res = requests.get(player_url, headers=headers, timeout=5)
            match = re.search(r"this\.baseStreamUrl\s*=\s*'(.*?)'", res.text)
            if match:
                base = match.group(1)
                return f"{base}{stream_id}/playlist.m3u8"
        except:
            pass
        return None

    domain = find_active_domain()
    if not domain:
        return results
    print(f"XSport Domain: {domain}")

    try:
        response = requests.get(domain, headers=headers, timeout=10)
        for cid in channel_ids:
            pattern = rf'data-url="(.*?id={cid}.*?)"'
            match = re.search(pattern, response.text)
            if match:
                player_link = match.group(1)
                final_url = get_stream_url(player_link, cid)
                if final_url:
                    clean_name = cid.replace("x", "").replace("-", " ").upper()
                    if "BEINSPORTS" in clean_name:
                        clean_name = clean_name.replace("BEINSPORTS", "beIN Sports")
                    entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO}" group-title="XSport-Panel", {clean_name}\n#EXTVLCOPT:http-referer={domain}\n{final_url}'
                    results.append(entry)
    except:
        pass
    return results


# ============================================
# 6. PALAZZO (YENİ AES SİSTEM)
# ============================================

def restore_str(arr, offset):
    return "".join(chr(int(x) - offset) for x in arr)


def decrypt_palazzo(html_content):
    try:
        val_match = re.search(r'data-val="([^"]+)"', html_content)
        enc_match = re.search(r'data-enc="([^"]+)"', html_content)
        key_match = re.search(r'var keyArray\s*=\s*\[(.*?)\]', html_content, re.S)
        stream_match = re.search(r"var primaryStream\s*=\s*decryptUrl\('([^']+)'\)", html_content)

        if not all([val_match, enc_match, key_match, stream_match]):
            return None

        offset = int(base64.b64decode(val_match.group(1)).decode())

        iv_array = json.loads(base64.b64decode(enc_match.group(1)).decode())

        key_array = [int(x.strip()) for x in key_match.group(1).split(',')]

        key = restore_str(key_array, offset).encode("utf-8")
        iv = restore_str(iv_array, offset).encode("utf-8")

        encrypted_data = base64.b64decode(stream_match.group(1))

        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)

        final_url = decrypted.decode("utf-8").strip()

        if final_url.startswith("http"):
            return final_url

        return None

    except Exception as e:
        print("Decrypt Hata:", e)
        return None


def get_palazzo_domain():
    print("🔎 Palazzo aktif domain aranıyor...")
    base_pattern = "https://palazzocanli{}.com"

    def check(i):
        url = base_pattern.format(i)
        try:
            r = requests.get(url, headers=HEADERS, timeout=5, verify=False)
            if (
                r.status_code == 200
                and (
                    "player2.php" in r.text
                    or "primaryStream" in r.text
                    or "decryptUrl" in r.text
                )
            ):
                return url
        except:
            pass
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = [ex.submit(check, i) for i in range(28, 201)]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                return res

    return None


def get_palazzo_template(main_html):
    patterns = [
        r'"url":"(https?:\/\/[^"]+?player2\.php\?[^"]*?id=)',
        r'(https:\/\/[^"\']+player2\.php\?[^"\']*?id=)',
        r'(https:\/\/[^"\']+\/player\/player2\.php\?[^"\']*?id=)',
        r'(https:\/\/[^"\']+\/embed\/player2\.php\?[^"\']*?id=)'
    ]

    for pat in patterns:
        m = re.search(pat, main_html)
        if m:
            template = m.group(1)
            template = template.replace('\\/', '/')
            template = template.replace('&amp;', '&')
            print("🎯 Player template bulundu:", template)
            return template

    return None


def fetch_palazzo_channel(cid, player_template, active_site):
    try:
        full_url = f"{player_template}{cid}"
        p_headers = HEADERS.copy()
        
        # PLAYERA BAĞLANIRKEN PALAZZO'NUN GÜNCEL DOMAINİ (active_site) REFERER/ORIGIN KULLANILIYOR
        p_headers["Referer"] = active_site + "/"
        p_headers["Origin"] = active_site

        r = requests.get(full_url, headers=p_headers, timeout=10, verify=False)
        stream = decrypt_palazzo(r.text)

        return cid, stream

    except Exception as e:
        print("FAIL:", cid, e)
        return cid, None


def get_renconnect_content():
    print("--- 6. Palazzo AES Bot ---")

    channels = [
        ("601", "beIN Sports 1"),
        ("602", "beIN Sports 2"),
        ("603", "beIN Sports 3"),
        ("604", "beIN Sports 4"),
        ("605", "beIN Sports 5"),
        ("607", "S Sport 1"),
        ("608", "S Sport 2"),
        ("609", "Smart Spor 1"),
        ("610", "Smart Spor 2"),
        ("701", "Tivibu Spor 1"),
        ("702", "Tivibu Spor 2"),
        ("703", "Tivibu Spor 3"),
        ("704", "Tivibu Spor 4"),
        ("beinsportshaber", "beIN Haber"),
        ("eurosport1", "Eurosport 1"),
        ("eurosport2", "Eurosport 2"),
    ]

    results_map = {}

    active_site = get_palazzo_domain()
    if not active_site:
        print("❌ Palazzo: Site bulunamadı")
        return []

    print("🌐 Palazzo Domain:", active_site)

    r = requests.get(active_site, headers=HEADERS, timeout=10, verify=False)
    player_template = get_palazzo_template(r.text)

    if not player_template:
        print("❌ Palazzo: Template bulunamadı")
        return []

    # PLAYER LİNKİNİN DOMAINİNİ AYIR (M3U ÇIKTISINDA YAYINI OYNATMAK İÇİN REF OLARAK KULLANILACAK)
    parsed_uri = urlparse(player_template)
    player_domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
    print(f"🔑 M3U Player Ref Domaini: {player_domain}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futures = [
            # Yayın çekilirken active_site kullanılıyor
            ex.submit(fetch_palazzo_channel, cid, player_template, active_site)
            for cid, _ in channels
        ]

        for f in concurrent.futures.as_completed(futures):
            cid, stream = f.result()
            name = next(n for c, n in channels if c == cid)

            if not stream:
                print("❌ FAIL:", name)
                continue

            print("✅ OK:", name)

            # M3U ÇIKTISINDA O PLAYER LİNKİ (player_domain) REF ORIGIN OLUYOR
            entry = (
                f'#EXTINF:-1 '
                f'tvg-logo="{STATIC_LOGO}" '
                f'group-title="RenConnect-Panel",{name}\n'
                f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}\n'
                f'#EXTVLCOPT:http-referrer={player_domain}/\n'
                f'#EXTVLCOPT:http-origin={player_domain}\n'
                f'{stream}'
            )

            results_map[cid] = entry

    # Sıralı çıktı
    ordered_results = []
    for cid, _ in channels:
        if cid in results_map:
            ordered_results.append(results_map[cid])

    return ordered_results


# ============================================
# 7. BONUS TV (ZEUS)
# ============================================

def get_bonus_content():
    print("--- 7. Bonus TV (Zeus) ---")
    results = []

    BASE_DOMAIN_PATTERN = "zeustv{}.vip"
    START_INDEX = 257
    END_INDEX = 500

    CHANNELS = {
        'b1': 'beIN Spor 1', 'b1local': 'beIN Spor 1 YDK',
        'b2': 'beIN Spor 2', 'b3': 'beIN Spor 3',
        'b4': 'beIN Spor 4', 'b5': 'beIN Spor 5',
        'b1max': 'beIN Max 1', 'b2max': 'beIN Max 2',
        's1': 'S Spor 1', 's2': 'S Spor 2',
        'smart1': 'Smart Spor 1', 'smart2': 'Smart Spor 2',
        'tivibu': 'Tivibu Spor', 'tivibu1': 'Tivibu Spor 1',
        'tivibu2': 'Tivibu Spor 2', 'tivibu3': 'Tivibu Spor 3',
        'euro1': 'Euro Spor 1', 'euro2': 'Euro Spor 2',
        'sifirtv': 'Sıfırtv'
    }

    def check_site(index):
        url = f"https://{BASE_DOMAIN_PATTERN.format(index)}"
        try:
            r = requests.get(url + "/", headers=HEADERS, timeout=5, verify=False, allow_redirects=True)
            if r.status_code == 200:
                return url
        except:
            return None
        return None

    def get_base_url_from_page(active_domain):
        page_url = f"{active_domain}/ch.html?id=b1"
        try:
            response = requests.get(page_url, headers=HEADERS, timeout=10, verify=False)
            response.raise_for_status()
            html_content = response.text

            patterns = [
                r'atob\("([A-Za-z0-9+/=]+)"\)',
                r'var\s+\w+\s*=\s*"([A-Za-z0-9+/=]+)"',
                r'src="([A-Za-z0-9+/=]+)"'
            ]

            base64_string = None
            for pattern in patterns:
                match = re.search(pattern, html_content)
                if match:
                    base64_string = match.group(1)
                    break

            if base64_string:
                try:
                    decoded_bytes = base64.b64decode(base64_string)
                    decoded_url = decoded_bytes.decode('utf-8')
                    if not decoded_url.endswith('/'):
                        decoded_url += '/'
                    return decoded_url
                except:
                    pass
        except:
            pass
        return None

    active_url = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        futures = [executor.submit(check_site, i) for i in range(START_INDEX, END_INDEX + 1)]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                active_url = result
                executor.shutdown(wait=False, cancel_futures=True)
                break

    if not active_url:
        return results

    print(f"Bonus TV Domain: {active_url}")

    base_video_url = get_base_url_from_page(active_url)
    if not base_video_url:
        return results

    for channel_id, channel_name in CHANNELS.items():
        stream_url = f"{base_video_url}{channel_id}/index.m3u8"
        entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO}" group-title="Bonustv", {channel_name}\n{stream_url}'
        results.append(entry)

    return results


# ============================================
# MAIN
# ============================================

def main():
    print("🔥 DeaTHLesS-Bot v3.3 Başladı")

    all_content = ["#EXTM3U"]
    all_content.extend(get_selcuk_content())
    all_content.extend(get_atom_content())
    all_content.extend(get_trgoals_content())
    all_content.extend(get_andro_content())
    all_content.extend(get_xsport_content())
    all_content.extend(get_renconnect_content())
    all_content.extend(get_bonus_content())

    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write("\n".join(all_content))

        full_path = os.path.abspath(OUTPUT_FILENAME)
        total_channels = len(all_content) - 1

        print("\n✅ Tamamlandı!")
        print(f"📄 Dosya: {OUTPUT_FILENAME}")
        print(f"📺 Kanal Sayısı: {total_channels}")
        print(f"📂 Konum: {full_path}")

    except IOError as e:
        print(f"\n❌ Hata: {e}")


if __name__ == "__main__":
    main()
