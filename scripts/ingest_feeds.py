"""ingest_feeds.py

Merge external phishing feeds or local CSVs into dataset.csv safely.

Usage examples:
  # Merge local feed files
  python scripts/ingest_feeds.py --local feeds/phishtank_sample.csv feeds/openphish.csv

  # Download and merge public feed CSVs (if accessible)
  python scripts/ingest_feeds.py --urls https://example.com/phish.csv

The script will create a timestamped backup of `dataset.csv` before overwriting.
"""
import argparse
import csv
import os
import sys
import time
from datetime import datetime
import pandas as pd
import requests

DEFAULT_DATASET = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset.csv')


def read_csv_path(path):
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        print(f"Failed to read CSV {path}: {e}")
        return pd.DataFrame()


def download_csv(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        # Try to read into pandas from text
        from io import StringIO
        return pd.read_csv(StringIO(resp.text))
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return pd.DataFrame()


def normalize_feed(df, assumed_phishing=1):
    # Try to find a URL column
    candidates = [c for c in df.columns if 'url' in c.lower()]
    if not candidates and len(df.columns) >= 1:
        # take first column as URL
        candidates = [df.columns[0]]

    if not candidates:
        return pd.DataFrame(columns=['url', 'is_phishing'])

    url_col = candidates[0]

    # Determine label column if present
    label_col = None
    for c in df.columns:
        if c.lower() in ('is_phishing', 'label', 'phish', 'verified', 'status'):
            label_col = c
            break

    out = pd.DataFrame()
    out['url'] = df[url_col].astype(str).str.strip()
    if label_col:
        # try to coerce to 0/1
        out['is_phishing'] = df[label_col].apply(lambda v: 1 if str(v).strip().lower() in ('1','true','phish','yes','y') else 0)
    else:
        out['is_phishing'] = assumed_phishing

    # drop empty URLs
    out = out[out['url'].notna() & (out['url'] != '')]
    return out


def backup_dataset(dataset_path):
    if not os.path.exists(dataset_path):
        return
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = dataset_path.replace('.csv', f'_backup_{ts}.csv')
    try:
        os.replace(dataset_path, backup)
        print(f"Backed up {dataset_path} to {backup}")
    except Exception as e:
        print(f"Failed to backup {dataset_path}: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--urls', nargs='*', help='CSV URLs to download and ingest')
    parser.add_argument('--local', '--local-files', nargs='*', dest='local', help='Local CSV file paths to ingest')
    parser.add_argument('--dataset', default=DEFAULT_DATASET, help='Path to dataset.csv to merge into')
    parser.add_argument('--assume-feed-phish', type=int, choices=(0,1), default=1, help='If a feed has no label column, assume rows are phishing (1) or benign (0)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be merged without writing dataset.csv')
    args = parser.parse_args()

    inputs = []
    if args.urls:
        for u in args.urls:
            print(f"Downloading {u}...")
            df = download_csv(u)
            if not df.empty:
                inputs.append(('url', u, df))

    if args.local:
        for p in args.local:
            p = os.path.expanduser(p)
            print(f"Reading local file {p}...")
            df = read_csv_path(p)
            if not df.empty:
                inputs.append(('local', p, df))

    if not inputs:
        print('No inputs found. Provide --urls or --local files.')
        sys.exit(1)

    parts = []
    for typ, src, df in inputs:
        print(f"Normalizing feed from {src}...")
        normalized = normalize_feed(df, assumed_phishing=args.assume_feed_phish)
        if normalized.empty:
            print(f"No URLs found in {src}")
            continue
        parts.append(normalized)

    if not parts:
        print('No valid feed data to merge.')
        sys.exit(1)

    merged_new = pd.concat(parts, ignore_index=True)
    merged_new.dropna(subset=['url'], inplace=True)
    merged_new['url'] = merged_new['url'].str.strip()
    merged_new.drop_duplicates(subset=['url'], inplace=True)

    # Load existing dataset if present
    if os.path.exists(args.dataset):
        existing = pd.read_csv(args.dataset)
        if 'url' not in existing.columns or 'is_phishing' not in existing.columns:
            print(f"Existing dataset {args.dataset} does not have required columns. Aborting.")
            sys.exit(1)
        combined = pd.concat([existing, merged_new], ignore_index=True)
    else:
        combined = merged_new

    # Deduplicate by URL keeping the latest (last occurrence)
    combined['url'] = combined['url'].str.strip()
    combined.drop_duplicates(subset=['url'], keep='last', inplace=True)

    print(f"Prepared combined dataset with {len(combined)} rows (new feeds contributed {len(merged_new)} rows).")

    if args.dry_run:
        print(combined.head(50).to_string(index=False))
        print('Dry-run; dataset not written.')
        sys.exit(0)

    # Backup existing dataset
    if os.path.exists(args.dataset):
        backup_dataset(args.dataset)

    combined.to_csv(args.dataset, index=False)
    print(f"Wrote merged dataset to {args.dataset}")


if __name__ == '__main__':
    main()
