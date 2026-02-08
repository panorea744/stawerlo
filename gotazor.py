import requests
import re
import base64
import os

# --- AYARLAR ---
BASE_URL_PATTERN = "https://palazzocanli{}.com"
GITHUB_FOLDER = "gotazor"

# Hangi ID'nin hangi Gotazor dosyasına gideceği
# 601-605 Beinler, 607-608 S Sportlar, 701-704 Tivibular
KANAL_LISTESI = {
    "601": 1, "602": 2, "603": 3, "604": 4, "605": 5,
    "607": 6, "608": 7,
    "701": 8, "702": 9, "703": 10, "704": 11
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def aktif_domain_bul():
    for i in range(25, 101):
        url = BASE_URL_PATTERN.format(i)
        try:
            res = requests.get(url, timeout=3, headers=headers)
            if res.status_code == 200: return url
        except: continue
    return None

def url_kalibi_al(aktif_site):
    """Herhangi bir kanaldan m3u8 yapısını çözer ve ID kısmını boşaltır."""
    res = requests.get(aktif_site, headers=headers)
    # Sitedeki herhangi bir player linkini bul (örn: id=607)
    match = re.search(r'data-stream="(https://.*?/player/player\.php\?id=(.*?))"', res.text)
    if not match: return None
    
    player_url = match.group(1)
    current_id = match.group(2)
    
    h = headers.copy()
    h["Origin"] = aktif_site
    h["Referer"] = aktif_site + "/"
    
    p_res = requests.get(player_url, headers=h)
    stream_match = re.search(r'var stream = atob\("(.*?)"\);', p_res.text)
    
    if stream_match:
        decoded = base64.b64decode(stream_match.group(1)).decode('utf-8')
        # Token ve expires kısmını at (Soru işaretinden sonrasını sil)
        temiz_url = decoded.split('?')[0]
        # URL içindeki mevcut ID'yi (örn: 607) bir joker ile değiştiriyoruz ki sonra 601, 602 yazabilelim
        # Örn: .../607/index.m3u8 -> .../{ID}/index.m3u8
        kalip = temiz_url.replace(f"/{current_id}/", "/{ID}/")
        return kalip
    return None

def main():
    if not os.path.exists(GITHUB_FOLDER): os.makedirs(GITHUB_FOLDER)

    aktif_site = aktif_domain_bul()
    if not aktif_site: 
        print("Site bulunamadı.")
        return

    url_kalip = url_kalibi_al(aktif_site)
    if not url_kalip:
        print("Kalıp URL çözülemedi.")
        return

    print(f"Kalıp oluşturuldu: {url_kalip}")

    for cid, no in KANAL_LISTESI.items():
        # Kalıptaki {ID} yerine gerçek kanal ID'sini koyuyoruz
        final_link = url_kalip.format(ID=cid)
        
        dosya_adi = f"{GITHUB_FOLDER}/Gotazor{no}.m3u8"
        content = (
            "#EXTM3U\n"
            "#EXT-X-VERSION:3\n"
            "#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,"
            "RESOLUTION=1920x1080,CODECS=\"avc1.640028,mp4a.40.2\",FRAME-RATE=25\n"
            f"{final_link}"
        )
        
        with open(dosya_adi, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Bitti: Gotazor{no}.m3u8 (ID: {cid})")

if __name__ == "__main__":
    main()
