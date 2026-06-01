import os
import json
import requests
from bs4 import BeautifulSoup
import re
import argparse

def get_latest_hackaday_episode():
    """Scrape the Hackaday tag page to find the latest episode number."""
    url = 'https://hackaday.com/tag/floss-weekly/'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.find_all('article')
        max_ep = 0
        for article in articles:
            title_tag = article.find('h1', class_='entry-title')
            if title_tag:
                title_text = title_tag.text.strip()
                match = re.search(r'FLOSS Weekly (?:Episode )?(\d+)', title_text, re.IGNORECASE)
                if match:
                    max_ep = max(max_ep, int(match.group(1)))
        return max_ep
    except Exception as e:
        print(f"Error fetching latest Hackaday episode: {e}")
        return None

def check_episode_status(ep_num, base_dir, verify_online=False, get_hackaday_url_fn=None):
    """
    Checks the status of a specific episode.
    If verify_online is True, fetches live metadata when local files are missing.
    Returns: status (str), missing_files (list)
    """
    ep_dir = os.path.join(base_dir, f"episodes/{ep_num:04d}")
    metadata_path = os.path.join(ep_dir, "metadata.json")
    
    local_has_dir = os.path.exists(ep_dir)
    local_has_meta = os.path.exists(metadata_path)
    
    local_media = {}
    if local_has_meta:
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                local_media = json.load(f).get("media", {})
        except Exception:
            pass

    has_audio = False
    has_video = False
    if local_has_dir:
        for f in os.listdir(ep_dir):
            if f.endswith('.mp3'): has_audio = True
            if f.endswith('.mp4'): has_video = True

    needs_online_verify = False
    if verify_online:
        needs_online_verify = True

    media = local_media
    online_found = True
    
    if needs_online_verify:
        media = {}
        import time
        if ep_num <= 761:
            import archive_twit
            data = archive_twit.get_twit_episode_data(ep_num)
            if data:
                media = data.get("media", {})
            else:
                online_found = False
            time.sleep(archive_twit.RATE_LIMIT_DELAY)
        else:
            import archive_hackaday
            if get_hackaday_url_fn:
                url = get_hackaday_url_fn(ep_num)
                if url:
                    data = archive_hackaday.get_hackaday_episode_data(ep_num, url)
                    if data:
                        media = data.get("media", {})
                    else:
                        online_found = False
                    time.sleep(archive_hackaday.CRAWL_RATE_LIMIT_DELAY_SEC)
                else:
                    online_found = False

    missing_files = []
    
    if verify_online and needs_online_verify and not online_found:
        return "Missing", ["Not found on remote site"]

    if not local_has_dir:
        missing_files.append("Directory")
    if not local_has_meta:
        missing_files.append("metadata.json")
        
    if media.get("audio") and not has_audio:
        missing_files.append("Audio (.mp3)")
    if media.get("video") and not has_video:
        missing_files.append("Video (.mp4)")

    if missing_files:
        # If we only miss files, it's Partial. If we miss Directory entirely, it's Missing.
        if "Directory" in missing_files:
            # If verify_online showed no media expected, but directory is missing, it's still missing locally
            return "Missing", missing_files
        return "Partial", missing_files
        
    return "Fully Archived", []

def main():
    parser = argparse.ArgumentParser(description="Audit FLOSS Weekly downloaded episodes.")
    parser.add_argument("--base-dir", type=str, default=".", help="Base directory containing the 'episodes' folder")
    parser.add_argument("--max-episode", type=int, help="Override the maximum episode to check")
    parser.add_argument("--verify-online", action="store_true", help="Fetch metadata from remote site if local files are missing to verify true expectations")
    args = parser.parse_args()

    print("Determining expected episodes...")
    max_ep = args.max_episode
    if not max_ep:
        print("Fetching latest episode from Hackaday...")
        max_ep = get_latest_hackaday_episode()
        
    if not max_ep:
        print("Failed to determine max episode. Defaulting to a safe known minimum (869).")
        max_ep = 869
        
    print(f"Total expected episodes: {max_ep}\n")

    stats_twit = { "Fully Archived": [], "Partial": {}, "Missing": [] }
    stats_hackaday = { "Fully Archived": [], "Partial": {}, "Missing": [] }

    hackaday_url_map = None
    if args.verify_online and max_ep > 761:
        print("Pre-crawling Hackaday to support online verification...")
        import archive_hackaday
        # Suppress prints from crawl_episodes if possible, or just let them run
        hackaday_url_map = archive_hackaday.crawl_episodes(list(range(762, max_ep + 1)))

    def get_hackaday_url(ep):
        return hackaday_url_map.get(ep) if hackaday_url_map else None

    print("Scanning local archive...")
    for ep_num in range(1, max_ep + 1):
        status, missing = check_episode_status(ep_num, args.base_dir, args.verify_online, get_hackaday_url)
        
        # Categorize by source
        if ep_num <= 761:
            target_stats = stats_twit
        else:
            target_stats = stats_hackaday
            
        if status == "Fully Archived":
            target_stats["Fully Archived"].append(ep_num)
        elif status == "Missing":
            target_stats["Missing"].append(ep_num)
        elif status == "Partial":
            target_stats["Partial"][ep_num] = missing

    def print_report(source_name, start_ep, end_ep, stats):
        total = end_ep - start_ep + 1
        print("\n" + "-"*40)
        print(f" {source_name.upper()} EPISODES ({start_ep}-{end_ep})")
        print("-"*40)
        print(f"Total Expected:   {total}")
        print(f"Fully Archived:   {len(stats['Fully Archived'])}")
        print(f"Partially Saved:  {len(stats['Partial'])}")
        print(f"Missing Entirely: {len(stats['Missing'])}")
        
        if stats["Partial"]:
            print(f"\n--- PARTIAL {source_name.upper()} EPISODES ---")
            for ep, missing in stats["Partial"].items():
                print(f"Episode {ep:04d}: Missing {', '.join(missing)}")

        if stats["Missing"]:
            print(f"\n--- MISSING {source_name.upper()} EPISODES ---")
            ranges = []
            start = None
            prev = None
            for ep in stats["Missing"]:
                if start is None:
                    start = ep
                    prev = ep
                elif ep == prev + 1:
                    prev = ep
                else:
                    ranges.append((start, prev))
                    start = ep
                    prev = ep
            if start is not None:
                ranges.append((start, prev))
                
            range_strs = []
            for s, e in ranges:
                if s == e:
                    range_strs.append(str(s))
                else:
                    range_strs.append(f"{s}-{e}")
            print(f"Missing: {', '.join(range_strs)}")

    print("\n" + "="*40)
    print("        ARCHIVE STATUS REPORT")
    print("="*40)
    
    print_report("TWiT", 1, min(761, max_ep), stats_twit)
    if max_ep > 761:
        print_report("Hackaday", 762, max_ep, stats_hackaday)

if __name__ == "__main__":
    main()
