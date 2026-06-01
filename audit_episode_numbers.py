
import requests
from bs4 import BeautifulSoup
import re
import time

BASE_URL = "https://twit.tv"
START_URL = "https://twit.tv/episodes?filter[shows]=1639"

def check_episodes():
    current_url = START_URL
    page_count = 0
    non_standard_episodes = []
    
    print(f"Starting audit at {START_URL}")

    while current_url:
        page_count += 1
        print(f"Scanning page {page_count}...")
        
        try:
            response = requests.get(current_url)
            response.raise_for_status()
            
            # Debug: dump first page HTML
            if page_count == 1:
                with open("debug_page.html", "wb") as f:
                    f.write(response.content)

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all episode links
            # Pattern: /shows/floss-weekly/episodes/<id>
            episode_links = soup.find_all('a', href=re.compile(r'/shows/floss-weekly/episodes/'))
            
            for link in episode_links:
                href = link.get('href')
                # Extract the ID part
                parts = href.split('/')
                if 'episodes' in parts:
                    ep_id = parts[parts.index('episodes') + 1]
                    # Remove query params if any (though usually clean in href)
                    ep_id = ep_id.split('?')[0]
                    
                    if not ep_id.isdigit():
                        if ep_id not in non_standard_episodes:
                            non_standard_episodes.append(ep_id)
                            print(f"Found non-standard episode ID: {ep_id}")

            # Find next page
            next_link = soup.find('a', class_='next')
            
            if next_link:
                href = next_link.get('href')
                print(f"Found next page link: {href}")
                current_url = requests.compat.urljoin(current_url, href)
            else:
                print("No next page link found.")
                current_url = None

            # Be nice to the server
            time.sleep(1)
            
        except Exception as e:
            print(f"Error on page {page_count}: {e}")
            break

    print("\nAudit Complete.")
    print(f"Scanned {page_count} pages.")
    if non_standard_episodes:
        print("Non-standard episode numbers found:")
        for ep in non_standard_episodes:
            print(f"- {ep}")
    else:
        print("No non-standard episode numbers found.")

if __name__ == "__main__":
    check_episodes()
