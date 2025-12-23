import requests
import urllib3
import os
import time

# SSL Hatalarını Kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- AYARLAR ---
HEADERS = {"user-agent": "okhttp/4.12.0"}
MAIN_URL = "https://m.prectv60.lol"
SW_KEY = "4F5A9C3D9A86FA54EACEDDD635185/c3c5bd17-e37b-4b94-a944-8a3688a30452"
DOSYA_ADI = "RecTV_MEGA_ARSIV.m3u"

# KATEGORİ TANIMLARI
MOVIES_CATS = {
    "Son Filmler":   "/api/movie/by/filtres/0/created/",
    "Aile":          "/api/movie/by/filtres/14/created/",
    "Aksiyon":       "/api/movie/by/filtres/1/created/",
    "Animasyon":     "/api/movie/by/filtres/13/created/",
    "Belgesel":      "/api/movie/by/filtres/19/created/",
    "Bilim Kurgu":   "/api/movie/by/filtres/4/created/",
    "Dram":          "/api/movie/by/filtres/2/created/",
    "Fantastik":     "/api/movie/by/filtres/10/created/",
    "Komedi":        "/api/movie/by/filtres/3/created/",
    "Korku":         "/api/movie/by/filtres/8/created/",
    "Macera":        "/api/movie/by/filtres/17/created/",
    "Romantik":      "/api/movie/by/filtres/5/created/"
}

CHANNEL_ENDPOINT = "/api/channel/by/filtres/0/0/"
SERIES_LIST_ENDPOINT = "/api/serie/by/filtres/0/created/"
SERIES_DETAIL_ENDPOINT = "/api/season/by/serie/"

def write_to_file(text):
    """Bulunan veriyi anında dosyaya yazar (RAM şişmesin diye)"""
    with open(DOSYA_ADI, "a", encoding="utf-8") as f:
        f.write(text)

def main():
    print("--- RecTV MEGA ARŞİV BAŞLATIYOR ---")
    print("NOT: Bulunan her şey anlık olarak dosyaya yazılacak.")
    print("İşlem uzun sürecek. Telefonu şarja tak :)\n")

    # Dosyayı sıfırla ve başlığı at
    with open(DOSYA_ADI, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

    # ---------------------------------------------------------
    # BÖLÜM 1: CANLI TV
    # ---------------------------------------------------------
    print("\n" + "="*30)
    print("BÖLÜM 1: CANLI TV KANALLARI TARANIYOR...")
    print("="*30)
    
    page = 0
    while True:
        url = f"{MAIN_URL}{CHANNEL_ENDPOINT}{page}/{SW_KEY}/"
        try:
            resp = requests.get(url, headers=HEADERS, verify=False, timeout=10)
            data = resp.json()
            if not data: break # Veri bittiyse çık

            buffer = ""
            count = 0
            for item in data:
                sources = item.get("sources", [])
                if sources:
                    link = sources[0].get("url")
                    if link and "http" in link:
                        title = item.get("title", "Kanal").replace(",", " ")
                        img = item.get("image", "")
                        tid = item.get("id", "")
                        
                        buffer += f'#EXTINF:-1 tvg-id="{tid}" tvg-name="{title}" tvg-logo="{img}" group-title="Canlı TV",{title}\n'
                        buffer += f'#EXTVLCOPT:http-user-agent=okhttp/4.12.0\n{link}\n'
                        count += 1
            
            write_to_file(buffer)
            print(f" > Canlı TV Sayfa {page} bitti. (+{count} kanal)")
            page += 1
        except Exception as e:
            print(f"Hata (TV Sayfa {page}): {e}")
            page += 1
            if page > 100: break # Sonsuz döngü önlemi

    # ---------------------------------------------------------
    # BÖLÜM 2: FİLMLER
    # ---------------------------------------------------------
    print("\n" + "="*30)
    print("BÖLÜM 2: FİLMLER TARANIYOR...")
    print("="*30)

    for cat_name, endpoint in MOVIES_CATS.items():
        print(f"\n>>> Kategori: {cat_name}")
        page = 0
        while True:
            url = f"{MAIN_URL}{endpoint}{page}/{SW_KEY}/"
            try:
                resp = requests.get(url, headers=HEADERS, verify=False, timeout=10)
                data = resp.json()
                if not data: break

                buffer = ""
                count = 0
                for item in data:
                    sources = item.get("sources", [])
                    if sources:
                        link = sources[0].get("url")
                        if link and "http" in link:
                            title = item.get("title", "Film").replace(",", " ")
                            img = item.get("image", "")
                            tid = item.get("id", "")
                            
                            buffer += f'#EXTINF:-1 tvg-id="{tid}" tvg-name="{title}" tvg-logo="{img}" group-title="Film - {cat_name}",{title}\n'
                            buffer += f'#EXTVLCOPT:http-user-agent=okhttp/4.12.0\n{link}\n'
                            count += 1
                
                write_to_file(buffer)
                print(f"   > Sayfa {page} eklendi. (+{count} film)")
                page += 1
            except Exception as e:
                print(f"   > Hata (Sayfa {page}): {e}")
                time.sleep(1)
                page += 1
                if page > 500: break

    # ---------------------------------------------------------
    # BÖLÜM 3: DİZİLER (EN UZUN KISIM)
    # ---------------------------------------------------------
    print("\n" + "="*30)
    print("BÖLÜM 3: DİZİLER TARANIYOR (BU UZUN SÜRECEK)...")
    print("="*30)

    series_page = 0
    while True:
        list_url = f"{MAIN_URL}{SERIES_LIST_ENDPOINT}{series_page}/{SW_KEY}/"
        try:
            print(f"\n--- Dizi Listesi Sayfa {series_page} ---")
            resp = requests.get(list_url, headers=HEADERS, verify=False, timeout=10)
            series_list = resp.json()
            if not series_list: break

            for serie in series_list:
                s_id = serie.get("id")
                s_title = serie.get("title", "Dizi").strip()
                s_img = serie.get("image", "")
                
                # Detayları Çek
                detail_url = f"{MAIN_URL}{SERIES_DETAIL_ENDPOINT}{s_id}/{SW_KEY}/"
                try:
                    # Sunucuyu üzmemek için minik bekleme
                    # time.sleep(0.1)
                    
                    d_resp = requests.get(detail_url, headers=HEADERS, verify=False, timeout=10)
                    seasons = d_resp.json()
                    
                    if seasons:
                        buffer = ""
                        ep_count = 0
                        for season in seasons:
                            s_name = season.get("title", "Sezon ?")
                            for ep in season.get("episodes", []):
                                sources = ep.get("sources", [])
                                if sources:
                                    link = sources[0].get("url")
                                    if link and "http" in link:
                                        ep_name = ep.get("title", "Bölüm ?")
                                        full_title = f"{s_title} - {s_name} - {ep_name}"
                                        
                                        # Grup Title: Dizinin Adı (Klasörleme için)
                                        buffer += f'#EXTINF:-1 tvg-id="{s_id}" tvg-name="{full_title}" tvg-logo="{s_img}" group-title="{s_title}",{full_title}\n'
                                        buffer += f'#EXTVLCOPT:http-user-agent=okhttp/4.12.0\n{link}\n'
                                        ep_count += 1
                        
                        write_to_file(buffer)
                        print(f" > {s_title}: {ep_count} bölüm eklendi.")
                
                except Exception as e:
                    print(f" ! Hata ({s_title}): {e}")

            series_page += 1

        except Exception as e:
            print(f"Ana Döngü Hatası: {e}")
            break

    print("\n" + "="*40)
    print(f"TÜM İŞLEMLER BİTTİ! DOSYA: {os.path.abspath(DOSYA_ADI)}")
    print("="*40)

if __name__ == "__main__":
    main()
