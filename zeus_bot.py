import requests
import base64
import re
import os
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# --- KONFIGÜRASYON ---
BASE_DOMAIN_PATTERN = "zeustv{}.com"
START_INDEX = 229
END_INDEX = 500
REQUEST_TIMEOUT = 5  # saniye
GITHUB_FOLDER_NAME = "teyzeniyerim"
MASTER_M3U_FILENAME = "ventino.m3u" # Tekli ana oynatma listesi dosya adı

# Kanalların ID listesi (verdiğin listeden)
CHANNEL_IDS = [
    'b1', 'b1local', 'b2', 'b3', 'b4', 'bein5', 'b1max', 'b2max',
    's1', 's2', 'smart1', 'smart2', 'tivibu', 'tivibu1', 'tivibu2', 'tivibu3',
    'sifirtv', 'euro1', 'euro2', 'tabiiyedek', 'tabii1', 'tabii2', 'tabii3',
    'tabii4', 'tabii5', 'tabii6', 'xexxen', 'xexxen1'
]

# --- 1. FONKSİYON: AKTİF DOMAİNİ BUL ---
def find_active_domain():
    """229'dan 500'e kadar domainleri dener, ilk aktif olanın tam URL'sini döndürür."""
    print(f"🔍 {BASE_DOMAIN_PATTERN.format(START_INDEX)} ile {BASE_DOMAIN_PATTERN.format(END_INDEX)} arasında aktif domain taranıyor...")
    for i in range(START_INDEX, END_INDEX + 1):
        domain = BASE_DOMAIN_PATTERN.format(i)
        url = f"https://{domain}/"
        try:
            # Sadece başlığı kontrol et, hızlı olsun
            response = requests.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            if response.status_code == 200:
                print(f"✅ Aktif domain bulundu: {url}")
                return url.rstrip('/')  # Sonundaki slash'i temizle
            else:
                print(f"  {domain} yanıt verdi ama aktif değil (Status: {response.status_code})")
        except requests.ConnectionError:
            # Bağlantı hatası (domain aktif değil) sessizce geç
            pass
        except requests.Timeout:
            print(f"  {domain} zaman aşımına uğradı.")
        except Exception as e:
            print(f"  {domain} kontrol edilirken hata: {e}")

    print("❌ Hiçbir aktif domain bulunamadı.")
    return None

# --- 2. FONKSİYON: SAYFA KAYNAĞINDAN BASE64'Ü BUL VE ÇÖZ ---
def get_base_url_from_page(active_domain, channel_id='b1'):
    """Belirtilen kanal sayfasına gidip, sayfa kaynağından base64 kodu bulup çözer."""
    page_url = f"{active_domain}/ch.html?id={channel_id}"
    print(f"  📄 Sayfa kaynağı inceleniyor: {page_url}")
    try:
        response = requests.get(page_url, timeout=10)
        response.raise_for_status()  # 200 OK değilse hata fırlat
        html_content = response.text

        # Base64 kodunu bul (genellikle atob() içinde veya bir değişkende)
        patterns = [
            r'atob\("([A-Za-z0-9+/=]+)"\)',  # En yaygın: atob("base64...")
            r'var\s+\w+\s*=\s*"([A-Za-z0-9+/=]+)"',  # var _0x2a1 = "base64..."
            r'src="([A-Za-z0-9+/=]+)"'  # Bazen direkt src'te olabilir (daha az olası)
        ]

        base64_string = None
        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                base64_string = match.group(1)
                print(f"    🔑 Base64 kodu bulundu: {base64_string}")
                break

        if base64_string:
            try:
                # Base64'ü çöz (standart base64)
                decoded_bytes = base64.b64decode(base64_string)
                decoded_url = decoded_bytes.decode('utf-8')
                # URL düzgün değilse (örneğin sonunda / yoksa) düzelt
                if not decoded_url.endswith('/'):
                    decoded_url += '/'
                print(f"    ✅ Çözülen URL: {decoded_url}")
                return decoded_url
            except Exception as e:
                print(f"    ❌ Base64 çözülürken hata: {e}")
                return None
        else:
            print("    ❌ Sayfa kaynağında base64 kodu bulunamadı.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"    ❌ Sayfaya erişilemedi: {e}")
        return None

# --- 3. FONKSİYON: TÜM KANALLAR İÇİN AYRI .m3u8 DOSYALARINI OLUŞTUR ---
def create_m3u8_files(base_video_url, github_folder):
    """Verilen base video URL'sini kullanarak her kanal için ayrı bir .m3u8 dosyası oluşturur."""
    print(f"\n📁 '{github_folder}' klasöründe .m3u8 dosyaları oluşturuluyor...")

    os.makedirs(github_folder, exist_ok=True)

    m3u8_template = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25
{stream_url}
"""
    created_files = 0
    for channel_id in CHANNEL_IDS:
        stream_url = f"{base_video_url}{channel_id}/index.m3u8"
        filename = os.path.join(github_folder, f"{channel_id}.m3u8")

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(m3u8_template.format(stream_url=stream_url))
            created_files += 1
        except Exception as e:
            print(f"  ❌ {filename} oluşturulamadı: {e}")

    print(f"  🎉 Ayrı dosyalar tamamlandı! {created_files} dosya oluşturuldu.")

# --- 4. FONKSİYON: TEK BİR ANA .m3u DOSYASI OLUŞTUR ---
def create_master_m3u(base_video_url):
    """Tüm kanalları içeren tek bir ventino.m3u dosyası oluşturur (her seferinde sıfırdan)."""
    print(f"\n📋 '{MASTER_M3U_FILENAME}' dosyası sıfırdan oluşturuluyor...")
    
    try:
        # 'w' modu dosya varsa içini siler ve sıfırdan yazar
        with open(MASTER_M3U_FILENAME, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            
            for channel_id in CHANNEL_IDS:
                stream_url = f"{base_video_url}{channel_id}/index.m3u8"
                # Kanal ismini IPTV oynatıcılarda daha şık durması için büyük harf yapıyoruz
                channel_name = channel_id.upper()
                
                # M3U formatına uygun şekilde logo, grup başlığı ve kanal ismini yazdırıyoruz
                f.write(f'#EXTINF:-1 tvg-logo="https://i.hizliresim.com/8xzjgqv.jpg" group-title="DeaTHLesS", {channel_name}\n')
                f.write(f'{stream_url}\n')
                
        print(f"  ✅ {MASTER_M3U_FILENAME} başarıyla güncellendi/oluşturuldu!")
    except Exception as e:
        print(f"  ❌ {MASTER_M3U_FILENAME} oluşturulurken hata oluştu: {e}")

# --- ANA BOT ---
def main():
    print("🤖 Zeus TV M3U8 Botu Başlıyor...\n")

    # 1. Aktif domaini bul
    active_domain = find_active_domain()
    if not active_domain:
        print("❌ Aktif domain bulunamadığı için işlem durduruldu.")
        return

    # 2. Sayfa kaynağından base64'lü URL'yi bul
    base_video_url = get_base_url_from_page(active_domain, 'b1')
    if not base_video_url:
        print("❌ Video base URL'si alınamadığı için işlem durduruldu.")
        return

    # 3. Tüm kanallar için ayrı .m3u8 dosyalarını klasöre oluştur
    create_m3u8_files(base_video_url, GITHUB_FOLDER_NAME)
    
    # 4. Tüm kanalları içeren tekli ana m3u dosyasını oluştur
    create_master_m3u(base_video_url)
    
    print("\n🚀 Tüm işlemler sorunsuz tamamlandı!")

if __name__ == "__main__":
    main()
