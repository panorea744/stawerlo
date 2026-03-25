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
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

print(f"Connecting to: {url}")

driver = webdriver.Chrome(options=options)

try:
    driver.get(url)
    print("Page loaded. Waiting 10 seconds for network traffic...")
    time.sleep(10)

    logs = driver.get_log("performance")
    m3u8_links = set()

    for log in logs:
        try:
            log_json = json.loads(log["message"])["message"]
            
            if log_json["method"] == "Network.requestWillBeSent":
                request_url = log_json["params"]["request"]["url"]
                
                if ".m3u8" in request_url:
                    m3u8_links.add(request_url)
        except:
            continue

    print("\n--- CAPTURED M3U8 LINKS ---")
    if m3u8_links:
        for link in m3u8_links:
            print(link)
    else:
        print("No .m3u8 link found in network traffic.")

except Exception as e:
    print(f"Error: {e}")
finally:
    try:
        driver.quit()
    except:
    
        pass
