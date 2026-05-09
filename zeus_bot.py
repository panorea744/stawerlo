import requests
import re
import os

BASE_DOMAIN_PATTERN = "zeustv{}.vip"
START_INDEX = 262
END_INDEX = 500
REQUEST_TIMEOUT = 5  
GITHUB_FOLDER_NAME = "teyzeniyerim"
MASTER_M3U_FILENAME = "ventino.m3u" 

CHANNEL_IDS = [
    'b1', 'b1local', 'b2', 'b3', 'b4', 'bein5', 'b1max', 'b2max',
    's1', 's2', 'smart1', 'smart2', 'tivibu', 'tivibu1', 'tivibu2', 'tivibu3',
    'sifirtv', 'euro1', 'euro2', 'tabiiyedek', 'tabii1', 'tabii2', 'tabii3',
    'tabii4', 'tabii5', 'tabii6', 'xexxen', 'xexxen1'
]

def get_base_url_from_page(active_domain, channel_id='b1'):
    page_url = f"{active_domain}/ch.html?id={channel_id}"
    try:
        response = requests.get(page_url, timeout=10)
        response.raise_for_status()
        html_content = response.text

        match = re.search(r'var\s+streamUrl\s*=\s*["\']([^"\']+)["\']', html_content)

        if match:
            base_video_url = match.group(1)
            if not base_video_url.endswith('/'):
                base_video_url += '/'
            return base_video_url
        else:
            return None

    except requests.exceptions.RequestException:
        return None

def find_working_domain_and_url():
    for i in range(START_INDEX, END_INDEX + 1):
        domain = BASE_DOMAIN_PATTERN.format(i)
        url = f"https://{domain}"
        
        try:
            response = requests.get(url + "/", timeout=REQUEST_TIMEOUT, allow_redirects=True)
            if response.status_code == 200:
                base_video_url = get_base_url_from_page(url, 'b1')
                if base_video_url:
                    return url, base_video_url
        except Exception:
            pass

    return None, None

def create_m3u8_files(base_video_url, github_folder):
    os.makedirs(github_folder, exist_ok=True)

    m3u8_template = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25
{stream_url}
"""
    for channel_id in CHANNEL_IDS:
        stream_url = f"{base_video_url}{channel_id}/index.txt"
        filename = os.path.join(github_folder, f"{channel_id}.m3u8")

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(m3u8_template.format(stream_url=stream_url))
        except Exception:
            pass

def create_master_m3u(base_video_url):
    try:
        with open(MASTER_M3U_FILENAME, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for channel_id in CHANNEL_IDS:
                stream_url = f"{base_video_url}{channel_id}/index.txt"
                channel_name = channel_id.upper()
                f.write(f'#EXTINF:-1 tvg-logo="https://i.hizliresim.com/8xzjgqv.jpg" group-title="DeaTHLesS", {channel_name}\n')
                f.write(f'{stream_url}\n')
    except Exception:
        pass

def main():
    active_domain, base_video_url = find_working_domain_and_url()
    
    if not base_video_url:
        return

    create_m3u8_files(base_video_url, GITHUB_FOLDER_NAME)
    create_master_m3u(base_video_url)

if __name__ == "__main__":
    main()
