"""Download model artifacts from a provided base URL if they are missing.

Usage (recommended environment variables):
- MODEL_BASE_URL: base URL where model files are hosted (no trailing slash)
- MODEL_FILES: comma-separated filenames to download (e.g. phishing_model_20251208_145109.joblib,scaler_20251208_145109.joblib)

This script is intentionally small and uses streaming downloads.
"""
import os
import requests
import sys
from pathlib import Path
import zipfile

def download_models_if_missing(model_dir='models'):
    os.makedirs(model_dir, exist_ok=True)
    base = os.getenv('MODEL_BASE_URL')
    files = os.getenv('MODEL_FILES')
    if not base or not files:
        # Nothing configured
        return

    files = [f.strip() for f in files.split(',') if f.strip()]
    for fname in files:
        target = Path(model_dir) / fname
        if target.exists():
            continue
        url = f"{base.rstrip('/')}/{fname}"
        print(f"Downloading model {fname} from {url}...")
        try:
            r = requests.get(url, stream=True, timeout=30)
            r.raise_for_status()
            with open(target, 'wb') as fh:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
            print(f"Saved {target}")
            # If a zip archive was downloaded, attempt to extract its contents
            try:
                if str(target).lower().endswith('.zip'):
                    print(f"Extracting archive {target} to {model_dir}...")
                    with zipfile.ZipFile(target, 'r') as zf:
                        zf.extractall(path=model_dir)
                    print(f"Extraction complete: {target}")
            except Exception as e:
                print(f"Failed to extract {target}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Failed to download {url}: {e}", file=sys.stderr)
            # If download failed, do not raise to avoid crashing startup; caller may handle
    return

if __name__ == '__main__':
    download_models_if_missing()
