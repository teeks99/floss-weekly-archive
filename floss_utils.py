import os
import json
import requests
import re

def clean_text(text):
    """
    Cleans up text by removing extra whitespace and stripping distinct characters.
    """
    if not text:
        return ""
    # Replace non-breaking spaces and other whitespace with single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def save_episode_data(episode_data, target_dir):
    """
    Saves the episode metadata to a JSON file in the target directory.
    """
    os.makedirs(target_dir, exist_ok=True)
    metadata_path = os.path.join(target_dir, "metadata.json")
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(episode_data, f, indent=4, ensure_ascii=False)
    
    print(f"Saved metadata to {metadata_path}")

def download_file(url, target_path):
    """
    Downloads a file from the given URL to the target path.
    Skips download if the file already exists and has size > 0.
    """
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        print(f"File already exists: {target_path}")
        return

    print(f"Downloading {url} to {target_path}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Download complete: {target_path}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        # Clean up partial file if it exists
        if os.path.exists(target_path):
            os.remove(target_path)
