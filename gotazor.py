import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

url = "https://palazzocanli27.com/"

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--mute-audio")

# İşte IDM mantığı burada başlıyor: Ağ trafiğini dinleme yetkisi veriyoruz
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

print(f"-> {url} adresine bağlanılıyor...")

# Güncel Selenium (v4.6+) driver'ı kendisi indirir, sürüm hatası vermez
driver = webdriver.Chrome(options=options)

try:
    driver.get(url)
    print("-> Sayfa yüklendi. Yayının başlaması ve ağ paketlerinin düşmesi için 10 saniye bekleniyor...")
    time.sleep(10)

    # Tarayıcının arkasında dönen tüm ağ trafiği kayıtlarını çekiyoruz
    logs = driver.get_log("performance")
    m3u8_linkleri = set()

    for log in logs:
        try:
            log_json = json.loads(log["message"])["message"]
            # Sadece "Giden Ağ İsteklerini" (Network.requestWillBeSent) filtrele
            if log_json["method"] == "Network.requestWillBeSent":
                request_url = log_json["params"]["request"]["url"]
                # URL içinde .m3u8 geçiyorsa listeye ekle
                if ".m3u8" in request_url:
                    m3u8_linkleri.add(request_url)
        except:
            continue

    print("\n--- YAKALANAN M3U8 LİNKLERİ (IDM Mantığı) ---")
    if m3u8_linkleri:
        for link in m3u8_linkleri:
            print(link)
    else:
        print("Ağ trafiğinde .m3u8 uzantılı bir link bulunamadı.")

except Exception as e:
    print(f"Hata oluştu: {e}")
finally:
    driv
    er.quit()
