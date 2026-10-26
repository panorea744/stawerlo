import base64
import os
import re
import requests
import urllib3

# SSL uyarılarını bastır
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ENCRYPTED_URL = "aHR0cHM6Ly95dHViZS13YXJzLm15d2lyZS5vcmcvbm91dHViZS9wbGF5bGlzdC5tM3U="

def create_folder(folder_name="noutube1"):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def decrypt_url(encrypted_url):
    decrypted_bytes = base64.b64decode(encrypted_url)
    return decrypted_bytes.decode("utf-8")

def fetch_playlist(url):
    response = requests.get(url, verify=False)
    response.raise_for_status()
    return response.text

def parse_playlist(content):
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    channels = []
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            match = re.search(r",(.+)$", lines[i])
            if match and i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                channel_name = match.group(1).strip()
                channel_url = lines[i + 1].strip()
                channels.append((channel_name, channel_url))
    return channels

def safe_filename(name):
    return re.sub(r'[^a-zA-Z0-9._-]', '_', name)

def save_channel_as_m3u8(channel_name, stream_url, folder="noutube1"):
    filename = f"{folder}/{safe_filename(channel_name)}.m3u8"
    content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720
{stream_url}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {filename}")

def git_push(folder="noutube1"):
    # PAT_TOKEN ortam değişkeninden alınır
    pat_token = os.getenv("PAT_TOKEN")
    if not pat_token:
        print("Error: PAT_TOKEN environment variable not set.")
        return
    
    os.system("git config user.name 'seyityavuz'")
    os.system("git config user.email 'seyityavuz@users.noreply.github.com'")
    os.system(f"git add {folder}")
    os.system("git commit -m 'Update playlist channels via script' || echo 'No changes to commit'")
    os.system(f"git push https://x-access-token:{pat_token}@github.com/seyityavuz/yavuznet.git main")

def main(encrypted_url=ENCRYPTED_URL, folder="noutube1"):
    try:
        create_folder(folder)
        playlist_url = decrypt_url(encrypted_url)
        print(f"Fetching playlist from: {playlist_url}")
        playlist_content = fetch_playlist(playlist_url)
        channels = parse_playlist(playlist_content)
        
        if not channels:
            print("No channels found in playlist.")
            return
        
        for name, url in channels:
            save_channel_as_m3u8(name, url, folder)
        
        print(f"Successfully saved {len(channels)} channels.")
        
        # GitHub'a push et
        git_push(folder)
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
