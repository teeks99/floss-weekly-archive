import requests
from bs4 import BeautifulSoup
import os
import time
import argparse
import sys
import re
import json
import subprocess
from floss_utils import save_episode_data, download_file, clean_text

CRAWL_RATE_LIMIT_DELAY_SEC = 5
ARCHIVE_RATE_LIMIT_DELAY_SEC = 1200

def get_soup(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def crawl_episodes(target_episodes):
    """
    Crawls Hackaday tag pages to find URLs for target episodes.
    Returns a dict {episode_num: url}
    """
    found_episodes = {}
    page_num = 1
    
    # Optimization: If we have found all targets, we can stop.
    target_set = set(target_episodes)
    
    # Simple heuristic: If we see episodes significantly older than our min target, stop.
    min_target = min(target_episodes) if target_episodes else 0
    
    print("Crawling Hackaday for episode discovery...")
    
    os.makedirs("hackaday_indexes", exist_ok=True)
    
    while True:
        url = f"https://hackaday.com/tag/floss-weekly/page/{page_num}/"
        cache_path = os.path.join("hackaday_indexes", f"page_{page_num}.html")
        
        if os.path.exists(cache_path):
            print(f"Using cached index page: {cache_path}")
            with open(cache_path, 'rb') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
        else:
            print(f"Scanning {url}...")
            try:
                response = requests.get(url)
                response.raise_for_status()
                with open(cache_path, 'wb') as f:
                    f.write(response.content)
                soup = BeautifulSoup(response.content, 'html.parser')
            except requests.RequestException as e:
                print(f"Failed to fetch {url}: {e}")
                soup = None

        if not soup:
            break
            
        articles = soup.find_all('article')
        if not articles:
            print("No more articles found.")
            break
            
        page_min_episode = float('inf')
        
        for article in articles:
            title_tag = article.find('h1', class_='entry-title')
            if not title_tag:
                continue
                
            title_text = title_tag.text.strip()
            link = title_tag.find('a')['href']
            
            # Regex to match "FLOSS Weekly Episode <NUM>..." or "FLOSS Weekly <NUM>..."
            match = re.search(r'FLOSS Weekly (?:Episode )?(\d+)', title_text, re.IGNORECASE)
            if match:
                ep_num = int(match.group(1))
                page_min_episode = min(page_min_episode, ep_num)
                
                # Store if it's one we might need later (or now)
                # The user asked to keep a list of ALL encountered episodes to avoid re-crawling.
                # So we store everything we find.
                found_episodes[ep_num] = link
        
        # Check if we should stop crawling
        # If the newest episode on this page is older than our oldest target, we can probably stop.
        # (Assuming reverse chronological order)
        if page_min_episode < min_target:
             print(f"Reached episodes ({page_min_episode}) older than target ({min_target}). Stopping crawl.")
             break

        # Check if we have found all targets
        if target_set.issubset(found_episodes.keys()):
            print("Found all target episodes.")
            break
            
        page_num += 1
        time.sleep(CRAWL_RATE_LIMIT_DELAY_SEC)
        
    return found_episodes

def get_hackaday_episode_data(episode_num, url):
    print(f"Fetching metadata for Episode {episode_num} from {url}")
    soup = get_soup(url)
    if not soup:
        return None
        
    # Metadata
    title_tag = soup.find('h1', class_='entry-title')
    title = clean_text(title_tag.text) if title_tag else f"FLOSS Weekly {episode_num}"
    
    date_tag = soup.find('meta', property='article:published_time')
    date = date_tag['content'].split('T')[0] if date_tag else ""
    
    # Summary & Guests from content
    content_div = soup.find('div', class_='entry-content')
    summary = ""
    guests = []
    
    if content_div:
        # Summary: usually first paragraph
        p_tags = content_div.find_all('p', recursive=False)
        if p_tags:
            summary = clean_text(p_tags[0].text)
        
        # Guests
        text_content = content_div.get_text()
        guest_match = re.search(r'Guest:?\s+([^\n\.]+)', text_content)
        if guest_match:
            guests.append(clean_text(guest_match.group(1)))

        # Related Links / Topics
        related_links = []
        for ul in content_div.find_all('ul'):
            # simple heuristic to skip "places to follow" widget if it ends up in entry-content or similar footers
            ul_text = ul.get_text().lower()
            if "google podcasts" in ul_text or "spotify" in ul_text or "itunes" in ul_text:
                continue
                
            for li in ul.find_all('li'):
                # clean text of the list item
                item_text = clean_text(li.text)
                
                # extract first link if present
                a = li.find('a', href=True)
                url_link = a['href'] if a else None
                
                if url_link:
                    related_links.append({
                        "text": item_text,
                        "url": url_link
                    })
                elif item_text:
                     # Just text (unlikely for "links", but possible for "topics")
                     related_links.append({
                        "text": item_text,
                        "url": ""
                    })

    # Media Extraction
    audio_url = None
    video_url = None
    
    # Audio: Look for libsyn links or .mp3
    # Hackaday usually links to Libsyn mp3s
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '.mp3' in href:
            audio_url = href
            break # Take first mp3
            
    # Video: Look for YouTube iframe
    # or yt-dlp supported URL
    iframe = soup.find('iframe', src=re.compile(r'youtube\.com/embed'))
    if iframe:
        video_url = iframe['src']
    
    return {
        "episode_number": episode_num,
        "title": title,
        "date": date,
        "summary": summary,
        "guests": guests,
        "related_links": related_links,
        "source_url": url,
        "media": {
            "audio": audio_url,
            "video": video_url
        }
    }

def archive_episode(episode_num, url, base_dir):
    data = get_hackaday_episode_data(episode_num, url)
    if not data:
        return

    episode_dir = os.path.join(base_dir, f"episodes/{episode_num:04d}")
    os.makedirs(episode_dir, exist_ok=True)

    # Save Metadata
    save_episode_data(data, episode_dir)

    # Download Audio
    if data['media'].get('audio'):
        audio_path = os.path.join(episode_dir, f"floss{episode_num:04d}.mp3")
        download_file(data['media']['audio'], audio_path)

    # Download Video (yt-dlp)
    if data['media'].get('video'):
        video_path = os.path.join(episode_dir, f"floss{episode_num:04d}.mp4")
        if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
             print(f"Video already exists: {video_path}")
        else:
            print(f"Downloading video from {data['media']['video']}...")
            try:
                # Use yt-dlp to download best video+audio and merge to mp4
                cmd = [
                    "yt-dlp",
                    "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "--output", video_path,
                    "--remote-components", "ejs:github",
                ]
                
                # Add cookies if file exists
                # We copy to a temp file to avoid PermissionError if the source is read-only/symlink
                # and because yt-dlp tries to update the file.
                use_cookies = False
                temp_cookies = "yt_cookies_temp.txt"
                
                if os.path.exists("yt_cookies.txt"):
                    print("Using yt_cookies.txt")
                    import shutil
                    shutil.copy("yt_cookies.txt", temp_cookies)
                    cmd.extend(["--cookies", temp_cookies])
                    use_cookies = True
                
                cmd.append("--")
                cmd.append(data['media']['video'])
                
                try:
                    subprocess.run(cmd, check=True)
                    print(f"Video download complete: {video_path}")
                finally:
                    # Clean up temp cookies
                    if use_cookies and os.path.exists(temp_cookies):
                        os.remove(temp_cookies)

            except subprocess.CalledProcessError as e:
                print(f"Failed to download video: {e}")
            except Exception as e:
                print(f"Error running yt-dlp: {e}")
    else:
        print("No video found.")

def main():
    parser = argparse.ArgumentParser(description="Archive FLOSS Weekly episodes from Hackaday.")
    parser.add_argument("--start", type=int, default=762, help="Start episode number")
    parser.add_argument("--end", type=int, default=860, help="End episode number")
    parser.add_argument("--episodes", type=str, help="Comma-separated list of specific episodes to archive")
    parser.add_argument("--output-dir", type=str, default=".", help="Directory to save episodes")
    
    args = parser.parse_args()

    target_episodes = []
    if args.episodes:
        try:
            target_episodes = [int(e.strip()) for e in args.episodes.split(',')]
        except ValueError:
            print("Invalid episode list format.")
            sys.exit(1)
    else:
        target_episodes = list(range(args.start, args.end + 1))

    base_dir = args.output_dir
    
    # 1. Discover Episodes (Crawl)
    # Filter targets to those likely on Hackaday (>= ~760) just in case
    # valid_targets = [e for e in target_episodes if e >= 760] # Optional safety
    
    found_map = crawl_episodes(target_episodes)
    
    # 2. Archive
    for ep_num in target_episodes:
        print(f"\n--- Processing Episode {ep_num} ---")
        if ep_num in found_map:
            archive_episode(ep_num, found_map[ep_num], base_dir)
            time.sleep(ARCHIVE_RATE_LIMIT_DELAY_SEC)
        else:
            print(f"Episode {ep_num} not found during crawl.")

if __name__ == "__main__":
    main()
