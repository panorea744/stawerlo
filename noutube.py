import yt_dlp
import time
import os
import subprocess

CHANNELS = {
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

OUTPUT_DIR = "noutube"

def get_m3u8(channel_id, retries=5):
    url = f"https://www.youtube.com/channel/{channel_id}/live"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "best",
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },
        "http_headers": {
            "User-Agent": "com.google.android.youtube/17.31.35"
        }
    }

    for _ in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if "url" in info:
                    return info["url"]

                if "formats" in info:
                    for f in info["formats"]:
                        if f.get("protocol") == "m3u8":
                            return f.get("url")
        except:
            pass

        time.sleep(2)

    return None


def write_m3u8(name, m3u8_url):
    path = os.path.join(OUTPUT_DIR, f"{name}.m3u8")

    content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720
{m3u8_url}
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def git_push():
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "update m3u8"], check=True)
        subprocess.run(["git", "push"], check=True)
    except:
        pass


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for name, channel_id in CHANNELS.items():
        print(f"Checking: {name}")
        m3u8 = get_m3u8(channel_id)

        if m3u8:
            write_m3u8(name, m3u8)
            print(f"Saved: {name}")
        else:
            print(f"Failed: {name}")

    git_push()


if __name__ == "__main__":
    main()
