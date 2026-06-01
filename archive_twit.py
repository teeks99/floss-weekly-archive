import requests
from bs4 import BeautifulSoup
import os
import time
import argparse
import sys
from floss_utils import save_episode_data, download_file, clean_text

RATE_LIMIT_DELAY = 30  # Seconds

def get_twit_episode_data(episode_num):
    url = f"https://twit.tv/shows/floss-weekly/episodes/{episode_num}"
    print(f"Fetching metadata for Episode {episode_num} from {url}")
    
    try:
        response = requests.get(url)
        if response.status_code == 404:
            print(f"Episode {episode_num} not found (404).")
            return None
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch episode page: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Init data
    title = f"FLOSS Weekly {episode_num}"
    date = ""
    summary = ""
    guests = []
    
    # Media URLs
    audio_url = None
    video_url = None

    # 1. Try JSON-LD
    import json
    ld_json_tag = soup.find('script', type='application/ld+json')
    if ld_json_tag:
        try:
            data = json.loads(ld_json_tag.string)
            if 'name' in data:
                title = f"FLOSS Weekly {episode_num}: {data['name']}"
            if 'uploadDate' in data:
                date = data['uploadDate'].split('T')[0] # YYYY-MM-DD
            if 'description' in data:
                summary = clean_text(BeautifulSoup(data['description'], 'html.parser').text)
            
            # Check for VideoObject
            if data.get('@type') == 'VideoObject' and 'contentUrl' in data:
                 video_url = data['contentUrl']
        except Exception as e:
            print(f"Error parsing JSON-LD: {e}")

    # 2. HTML Fallbacks / Enhancements
    if not date:
        date_tag = soup.find('div', class_='field--name-field-air-date')
        date_item = date_tag.find('div', class_='field__item') if date_tag else None
        date = clean_text(date_item.text) if date_item else ""

    # Summary from explicit paragraph in episode-details if JSON description is too short/generic
    episode_details = soup.find('div', class_='episode-details')
    if episode_details:
        # The main summary is usually the first <p> that isn't inside other divs
        paragraphs = episode_details.find_all('p', recursive=False)
        if paragraphs:
            full_summary = "\n".join([clean_text(p.text) for p in paragraphs])
            if len(full_summary) > len(summary):
                summary = full_summary
        
        # Extract Guests
        guests_div = episode_details.find('div', class_='guests')
        if guests_div:
            for a in guests_div.find_all('a'):
                guests.append(clean_text(a.text))

    # 3. Scrape Download Options (Best way to confirm valid media links)
    download_div = soup.find('div', id='download-options')
    if download_div:
        for a in download_div.find_all('a'):
            href = a.get('href')
            if not href: continue
            if '.mp3' in href and not audio_url:
                audio_url = href
            if '.mp4' in href and not video_url:
                video_url = href

    # 4. Fallback for Audio Only (Audio is almost always present)
    if not audio_url:
        padded_num = f"{episode_num:04d}"
        audio_url = f"https://cdn.twit.tv/audio/floss/floss{padded_num}/floss{padded_num}.mp3"
    
    # Note: We do NOT fallback for Video. If it wasn't in JSON-LD or Download Options, assume it doesn't exist.

    media = {"audio": audio_url}
    if video_url:
        media["video"] = video_url

    return {
        "episode_number": episode_num,
        "title": title,
        "date": date,
        "summary": summary,
        "guests": guests,
        "source_url": url,
        "media": media
    }

def archive_episode(episode_num, base_dir):
    data = get_twit_episode_data(episode_num)
    if not data:
        return

    episode_dir = os.path.join(base_dir, f"episodes/{episode_num:04d}")
    os.makedirs(episode_dir, exist_ok=True)

    # Save Metadata
    save_episode_data(data, episode_dir)

    # Download Media
    if data['media'].get('audio'):
        audio_path = os.path.join(episode_dir, f"floss{episode_num:04d}.mp3")
        download_file(data['media']['audio'], audio_path)

    if data['media'].get('video'):
        video_path = os.path.join(episode_dir, f"floss{episode_num:04d}.mp4")
        download_file(data['media']['video'], video_path)
    else:
        print(f"No video found for Episode {episode_num}")

def main():
    parser = argparse.ArgumentParser(description="Archive FLOSS Weekly episodes from TWIT.")
    parser.add_argument("--start", type=int, default=1, help="Start episode number")
    parser.add_argument("--end", type=int, default=761, help="End episode number")
    parser.add_argument("--episodes", type=str, help="Comma-separated list of specific episodes to archive")
    parser.add_argument("--output-dir", type=str, default=".", help="Directory to save episodes (default: current directory)")
    
    args = parser.parse_args()

    episodes = []
    if args.episodes:
        try:
            episodes = [int(e.strip()) for e in args.episodes.split(',')]
        except ValueError:
            print("Invalid episode list format.")
            sys.exit(1)
    else:
        episodes = range(args.start, args.end + 1)

    base_dir = args.output_dir

    for ep_num in episodes:
        print(f"\n--- Processing Episode {ep_num} ---")
        archive_episode(ep_num, base_dir)
        time.sleep(RATE_LIMIT_DELAY)

if __name__ == "__main__":
    main()
