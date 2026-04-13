#!/usr/bin/env python3
import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

TOTAL = 1000
WORKERS = 30

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.ginikoturkish.com/"
}

ALLOWED_DOMAIN = "trn03.tulix.tv"

def check_channel(ch_id):

    url = f"https://ginikoturkish.com/xml/secure/plist.php?ch={ch_id}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=8)

        if r.status_code != 200 or "HlsStreamURL" not in r.text:
            return None

        text = r.text

        stream_url = None

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        last_isvod = None

        for i, line in enumerate(lines):

            if line == "isVOD" and i+1 < len(lines):
                last_isvod = lines[i+1]

            if line == "HlsStreamURL" and i+1 < len(lines):
                u = lines[i+1]

                if u.startswith("http") and last_isvod == "false":
                    stream_url = u
                    break

        if not stream_url:
            m = re.search(r'<key>isVOD</key>\s*<string>false</string>.*?<key>HlsStreamURL</key>\s*<string>(.*?)</string>', text, re.DOTALL)
            if m:
                stream_url = m.group(1)

        if not stream_url:
            return None

        # 🔴 DOMAIN FILTRE
        if ALLOWED_DOMAIN not in stream_url:
            return None

        name = None

        for i, line in enumerate(lines):
            if line == "name" and i+1 < len(lines) and not lines[i+1].startswith("http"):
                name = lines[i+1].replace(" - Live", "").strip()
                break

        if not name:
            m = re.search(r'<key>name</key>\s*<string>(.*?)</string>', text)
            name = m.group(1).replace(" - Live", "").strip() if m else f"Kanal {ch_id}"

        logo = None

        for i, line in enumerate(lines):
            if line == "logoUrlHD" and i+1 < len(lines) and lines[i+1].startswith("http"):
                logo = lines[i+1]
                break

        if not logo:
            m = re.search(r'<key>logoUrlHD</key>\s*<string>(.*?)</string>', text)
            logo = m.group(1) if m else f"https://www.giniko.com/logos/190x110/{ch_id}.jpg"

        print(f"✓ {ch_id}: {name}")

        return {
            "id": ch_id,
            "name": name,
            "logo": logo,
            "stream": stream_url,
            "xmlUrl": url
        }

    except:
        return None


def main():

    print(f"Tarama başlıyor: 1-{TOTAL}")

    results = []

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:

        futures = {executor.submit(check_channel, i): i for i in range(1, TOTAL+1)}

        done = 0

        for future in as_completed(futures):

            done += 1

            result = future.result()

            if result:
                results.append(result)

            if done % 50 == 0:
                print(f"[{done}/{TOTAL}] Bulunan: {len(results)} kanal")

    results.sort(key=lambda x: x["id"])

    with open("channels5.json","w",encoding="utf-8") as f:
        json.dump(results,f,ensure_ascii=False,indent=2)

    print(f"\nToplam {len(results)} kanal bulundu")


if __name__ == "__main__":
    main()
