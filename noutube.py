import requests
import re
import urllib.parse
import urllib3
import time
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

channels = {
    "Kemal-sunal": "UCoIUysIrvGxoDw-GkdOGjRw",
    "avrupa-yakasi": "UCgc3VJYdM_R8oKGRuXxUbKQ",
    "Trfilmler": "UCmw7e_6j2TSWCKeaZALjyuA",
    "Adanali": "UCRP2h7AKS4nnUho0pyBCHgw",
    "cennet-mahallesi": "UCOqe-z52nnpVSAe8Ds0fxaA",
    "seksenler": "UCYRPB4TbD2RYHlIQdLgEeYA",
    "aski-memnu": "UCIdiuKAg5xVZsvXDQbOG4cg",
    "zengin-kiz": "UCiT-eroqDoA3zct3OkzhEPA",
    "yedi-numara": "UC0GKelxahF1nHwKyGhfJVYA",
    "edho": "UCeLBNGSG9w5qEbzQqZjqjuw",
    "yaprak-dokumu": "UCi-nK74pBX9Ou66z1j7KYPQ",
    "medcezir": "UCN0lBmyyylw4D4Lmf2ymuJw",
    "soz-dizi": "UCJkBcPylctTT0_jVC5XMFIg",
    "kurtlar-vadisi-pusu": "UCz1UfNp9VFp9R1HEFn5PY5A",
    "dirilis-ertugrul": "UCrr2fV8yd6r8k-FZKGxDr9Q",
    "sakarya-firat": "UCJbc3MgMFKqsCwTdrjWvVzQ",
    "leyla-ile-mecnun": "UCmODRwQLSOr5GEG77Uf_zpQ",
    "behzatc": "UCH3WnhFSx9r850HJRRs16lQ",
    "kuzey-guney": "UC2sr0q_shuQKijWoebuRvcA",
    "guller-gunahlar": "UCalPDcmRPlpaaXgNg8csL5w",
    "sihirli-annem": "UC8rnNIpGh8n6ZpWVqOBaKUQ",
    "yesil-deniz": "UCPUpDCqAbk0F7_occqwOBTA",
    "gonul-dagi": "UC6zAMy6boneCLJzRKiiwzmQ",
    "yalan-dunya": "UCN2Q-lSzQa7RjrCxQZ8DzbA",
    "alemin-krali": "UC7X6WuvzdVTFtAAAly9ldcw",
    "Feriha": "UCtkp8YehDHBNJ63CS9xwIQg",
    "muhtesem-yuzyil": "UCkRY4J8G__K8SEWZRLbke-Q",
    "yasak-elma": "UC5TccbGxEeVMx9gL6wp9fOg",
    "son-yaz": "UCzYNcw7NI3KA2bimswFRY8g",
    "sokagin-cocuklari": "UCs6evkqlctpaWvPCrnIbYEQ",
    "kismetse-olur": "UCW0OoKDNMH7b6HcWINTqqzA",
    "tasacak-bu-deniz": "UCx7gLo8iS4ofgNfBENUxWDA",
    "sifir-bir": "UCPy8l1I_lSGSGyNZ2Zf2xrg",
    "Fatmagul": "UCmeIlUqcw49tOsE82LXz_zg",
    "abi-dizi": "UCSifzNCnyapTKmQPYs-SZvA",
    "kardeslerim": "UCZLOnq-F5zhTWNUDjcEYByw",
    "kurulus-osman": "UCGR1XmkoQedeJMT2ajRHvsw",
    "selena": "UCC_iReQZgbPtOBfn3bjNnPw",
    "bir-zamanlar-cukurova": "UCdWD3k5SQUGXpHDkioiTFCw",
    "bir-gece-masali": "UCjrEQgmIujyGJPID6I4K2jw",
    "guldur-guldur": "UCdlEXiVLTEvA280oyMvr8Kw",
    "kizilcik-serbeti": "UCRfLDCtkSwmTdwHrbmC78Xg",
    "kiralik-ask": "UCNIr3_nBs6ba2BS5076rSaQ",
    "hzyusuf": "UCOpKuda5Ld_oc0Gdr31knmA",
    "arkadasim-hosgeldin": "UCOYerJedhQqSyhXkev8QRFA",
    "Tolgshow": "UCfyPw7vYwIVb6OuDIf7qeOQ",
    "inci-taneleri": "UCUxSoTMNflf9TAlZbml7XMw"
}

# Hızlı hata alıp geçmesi için değerleri çok düşürdük
max_retries = 2
wait_time = 3
folder_name = "noutube"

os.makedirs(folder_name, exist_ok=True)

for name, live_id in channels.items():
    print(f"[{name}] isleniyor...")
    success = False
    
    for attempt in range(1, max_retries + 1):
        try:
            headers1 = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            # Timeout süresini 10 saniyeye çektik
            response1 = requests.get("https://ytdlp.online/", headers=headers1, verify=False, timeout=10)

            if "session" not in response1.cookies:
                print(f"  -> {attempt}. deneme: Session alinamadi. HTTP Kodu: {response1.status_code}")
                time.sleep(wait_time)
                continue

            token = response1.cookies.get("session")
            youtube_link = f"https://www.youtube.com/channel/{live_id}/live"
            encoded_command = urllib.parse.quote(f"--get-url {youtube_link}")
            stream_url = f"https://ytdlp.online/stream?command={encoded_command}"

            headers2 = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/event-stream",
                "Referer": "https://ytdlp.online/",
                "Cookie": f"session={token}"
            }

            response2 = requests.get(stream_url, headers=headers2, verify=False, timeout=10)
            text = response2.text

            manifest_match = re.search(r'data:\s*(https://manifest\.googlevideo\.com[^\s]+)', text)

            if manifest_match:
                final_link = manifest_match.group(1).strip()
                m3u8_content = f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n{final_link}"

                file_path = os.path.join(folder_name, f"{name}.m3u8")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(m3u8_content)
                
                print(f"[{name}] basariyla eklendi.")
                success = True
                break
            else:
                print(f"  -> {attempt}. deneme: Manifest linki bulunamadi.")
                
        except Exception as e:
            print(f"  -> {attempt}. deneme hatasi: {e}")
        
        if attempt < max_retries:
            time.sleep(wait_time)
    
    if not success:
        print(f"[{name}] Hata sebebiyle gecildi.\n")

print("Tum islemler tamamlandi.")
