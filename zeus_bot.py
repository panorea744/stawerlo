import requests
import re
import os

# --- KONFIGÜRASYON ---
BASE_DOMAIN_PATTERN = "zeustv{}.cfd"
START_INDEX = 269
END_INDEX = 500
REQUEST_TIMEOUT = 10  # GitHub Actions ağ gecikmelerine karşı 5'ten 10'a çıkarıldı
GITHUB_FOLDER_NAME = "teyzeniyerim1"
MASTER_M3U_FILENAME = "ventino.m3u" 

CHANNEL_IDS = [
    'b1', 'b1local', 'b2', 'b3', 'b4', 'bein5', 'b1max', 'b2max',
    's1', 's2', 'smart1', 'smart2', 'tivibu', 'tivibu1', 'tivibu2', 'tivibu3',
    'sifirtv', 'euro1', 'euro2', 'tabiiyedek', 'tabii1', 'tabii2', 'tabii3',
    'tabii4', 'tabii5', 'tabii6', 'xexxen', 'xexxen1'
]

# BOT ENGELİNİ AŞMAK İÇİN SAHTE TARAYICI KİMLİĞİ (ÇOK ÖNEMLİ)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive"
}

def find_working_domain_and_url():
    print(f"🔍 {BASE_DOMAIN_PATTERN.format(START_INDEX)} ile {BASE_DOMAIN_PATTERN.format(END_INDEX)} arasında aktif domain taranıyor...")
    print("⚡ Tarama ana sayfa yerine doğrudan ch.html?id=b1 üzerinden yapılıyor.")
    print("🛡️ Bot engeli aşmak için sahte tarayıcı (Chrome) kimliği kullanılıyor...\n")
    
    for i in range(START_INDEX, END_INDEX + 1):
        domain = BASE_DOMAIN_PATTERN.format(i)
        # Direkt ch.html sayfasına gidiyoruz
        page_url = f"https://{domain}/ch.html?id=b1"
        
        try:
            # HEADERS parametresini ekleyerek sitenin bizi engellemesini önlüyoruz
            response = requests.get(page_url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            
            if response.status_code == 200:
                print(f"✅ Aktif sayfa bulundu: {page_url}")
                
                # Sayfa kaynağında streamUrl arıyoruz
                html_content = response.text
                match = re.search(r'var\s+streamUrl\s*=\s*["\']([^"\']+)["\']', html_content)

                if match:
                    base_video_url = match.group(1)
                    if not base_video_url.endswith('/'):
                        base_video_url += '/'
                    print(f"    ✅ Çözülen Base URL: {base_video_url}")
                    return f"https://{domain}", base_video_url
                else:
                    print("    ⚠️ Sayfa aktif ama 'streamUrl' kodu bulunamadı. Sonraki domaine geçiliyor...")
            elif response.status_code in [403, 401]:
                # İlk denemede eğer WAF veya Cloudflare engellerse loglarda görmek için:
                if i == START_INDEX:
                    print(f"    [!] {domain} için {response.status_code} hatası alındı (GitHub IP'si engelleniyor olabilir).")
            
        except requests.ConnectionError:
            pass
        except requests.Timeout:
            pass
        except Exception:
            pass

    print("\n❌ Gerekli kodu içeren hiçbir aktif domain bulunamadı.")
    return None, None

def create_m3u8_files(base_video_url, github_folder):
    print(f"\n📁 '{github_folder}' klasöründe dosyalar oluşturuluyor...")
    os.makedirs(github_folder, exist_ok=True)

    m3u8_template = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25
{stream_url}
"""
    created_files = 0
    for channel_id in CHANNEL_IDS:
        # DİKKAT: m3u8 yerine txt uzantısı ekleniyor
        stream_url = f"{base_video_url}{channel_id}/index.txt"
        
        # Oluşturulacak dosya adı yine .m3u8 kalıyor
        filename = os.path.join(github_folder, f"{channel_id}.m3u8")

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(m3u8_template.format(stream_url=stream_url))
            created_files += 1
        except Exception as e:
            print(f"  ❌ {filename} oluşturulamadı: {e}")

    print(f"  🎉 Ayrı dosyalar tamamlandı! {created_files} dosya oluşturuldu.")

def create_master_m3u(base_video_url):
    print(f"\n📋 '{MASTER_M3U_FILENAME}' dosyası sıfırdan oluşturuluyor...")
    try:
        with open(MASTER_M3U_FILENAME, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for channel_id in CHANNEL_IDS:
                # DİKKAT: m3u8 yerine txt uzantısı ekleniyor
                stream_url = f"{base_video_url}{channel_id}/index.txt"
                channel_name = channel_id.upper()
                
                f.write(f'#EXTINF:-1 tvg-logo="https://i.hizliresim.com/8xzjgqv.jpg" group-title="DeaTHLesS", {channel_name}\n')
                f.write(f'{stream_url}\n')
                
        print(f"  ✅ {MASTER_M3U_FILENAME} başarıyla güncellendi/oluşturuldu!")
    except Exception as e:
        print(f"  ❌ {MASTER_M3U_FILENAME} oluşturulurken hata oluştu: {e}")

def main():
    print("🤖 Zeus TV Botu Başlıyor...\n")

    active_domain, base_video_url = find_working_domain_and_url()
    
    if not base_video_url:
        print("❌ Video base URL'si alınamadığı için işlem durduruldu.")
        return

    create_m3u8_files(base_video_url, GITHUB_FOLDER_NAME)
    
    create_master_m3u(base_video_url)
    
    print("\n🚀 Tüm işlemler sorunsuz tamamlandı!")

if __name__ == "__main__":
    main()
