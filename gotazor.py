import undetected_chromedriver as uc
import re
import time

url = "https://benunluyumaskim.betconnectiframecdn1000.shop/player/player2.php?id=607"

headers = {
    "Origin": "https://benunluyumaskim.betconnectiframecdn1000.shop",
    "Referer": "https://benunluyumaskim.betconnectiframecdn1000.shop/",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Android WebView";v="146"',
    "sec-ch-ua-mobile": "?1",
    "Accept": "*/*",
    "sec-ch-ua-platform": '"Android"',
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.100 Safari/537.36"
}

print(f"Starting undetected_chromedriver for: {url}")

options = uc.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument(f'--user-agent={headers["User-Agent"]}')

try:
    driver = uc.Chrome(options=options)
    
    driver.execute_cdp_cmd('Network.enable', {})
    driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': headers})

    driver.get(url)
    
    print("Waiting 10 seconds for Cloudflare challenge to pass...")
    time.sleep(10)

    page_source = driver.page_source

    if "Cloudflare" in page_source or "Just a moment" in page_source:
        print("WARNING: Might be stuck on Cloudflare verification.")

    m3u8_links = set(re.findall(r'(https?://[^\s"\'<>]*\.m3u8[^\s"\'<>]*)', page_source))
    domains = set(re.findall(r'https?://([a-zA-Z0-9.-]+)', page_source))

    print("\n--- FOUND M3U8 LINKS ---")
    if m3u8_links:
        for link in m3u8_links:
            print(link)
    else:
        print("No direct .m3u8 link found.")

    print("\n--- FOUND DOMAINS ---")
    if domains:
        for domain in domains:
            print(domain)
    else:
        print("No other domains found.")

except Exception as e:
    print(f"Error: {e}")

finally:
    try:
        driver.quit()
    except:

        pass
