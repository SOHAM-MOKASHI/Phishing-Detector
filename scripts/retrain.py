"""retrain.py

Retrain the RandomForest model using dataset.csv and the existing `URLFeatureExtractor`.
By default it will perform live feature extraction (which hits the network). Use --offline
mode to run only URL-based feature extraction (faster and safe for bulk retraining).
"""
import argparse
import os
import sys
import traceback
import pandas as pd
from pathlib import Path

# Ensure we can import modules from the src/ directory even when running from scripts/
repo_root = Path(__file__).resolve().parents[1]
src_path = repo_root / 'src'
sys.path.insert(0, str(src_path))

from model_trainer import PhishingModelTrainer
from feature_extractor import URLFeatureExtractor

DEFAULT_DATASET = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset.csv')
DEFAULT_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')


def extract_features_batch(urls, extractor, offline_only=False):
    features = []
    for i, url in enumerate(urls):
        try:
            if offline_only:
                # Use only URL-level features and domain-level whois if available
                u_features = extractor._get_url_features(url)
                d_features = {'domain_age': -1, 'domain_expiry': -1, 'has_whois': False}
                features.append({
                    'url': url,
                    'url_features': u_features,
                    'domain_features': d_features,
                    'content_features': {'num_external_links': -1, 'has_form': False, 'has_password_field': False, 'num_iframes': -1, 'has_hidden_element': False},
                    'ssl_features': {'has_ssl': False, 'ssl_issuer': None, 'ssl_days_valid': -1}
                })
            else:
                f = extractor.extract_features(url)
                if f:
                    features.append(f)
        except Exception as e:
            print(f"Error extracting {url}: {e}")
            traceback.print_exc()
    return features


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', default=DEFAULT_DATASET, help='Path to dataset.csv')
    parser.add_argument('--model-dir', default=DEFAULT_MODEL_DIR, help='Output model directory')
    parser.add_argument('--offline', action='store_true', help='Extract only offline-safe features (no HTTP/WHOIS/SSL)')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of rows to use (for quick runs)')
    parser.add_argument('--cv', type=int, default=None, help='Number of cross-validation folds (if not provided, trains single model)')
    args = parser.parse_args()

    print(f"Loading dataset from {args.dataset}")
    if not os.path.exists(args.dataset):
        print(f"Dataset {args.dataset} not found")
        return

    try:
        df = pd.read_csv(args.dataset)
        if 'url' not in df.columns or 'is_phishing' not in df.columns:
            print("Dataset must contain 'url' and 'is_phishing' columns")
            return

        if args.limit:
            df = df.head(args.limit)

        urls = df['url'].tolist()
        labels = df['is_phishing'].tolist()

        print(f"Extracting features for {len(urls)} URLs (offline_only={args.offline})...")
        sys.stdout.flush()

        extractor = URLFeatureExtractor()
        features = extract_features_batch(urls, extractor, offline_only=args.offline)

        print(f"Extracted features for {len(features)} URLs")
        sys.stdout.flush()

        # Convert features list to DataFrame acceptable by trainer
        features_df = pd.DataFrame(features)
        if features_df.empty:
            print("No features extracted (features_df is empty). Aborting training.")
            return

        trainer = PhishingModelTrainer(model_path=args.model_dir)
        X = trainer.prepare_data(features_df)
        print(f"Prepared feature matrix with shape: {X.shape}")
        sys.stdout.flush()

        if X.shape[0] == 0:
            print("No numeric features available after preparation. Aborting training.")
            return

        y = pd.Series(labels[:len(X)])

        print(f"Training on {len(X)} samples...")
        sys.stdout.flush()
        
        if args.cv:
            print(f"\nPerforming {args.cv}-fold cross-validation...")
            metrics = trainer.train_model(X, y, cv=args.cv)
            print('\nCross-validation results:')
            # trainer.train_model currently returns a dict with mean/std floats and model_path
            if isinstance(metrics, dict) and 'cv_metric_mean_roc_auc' in metrics:
                mean = metrics.get('cv_metric_mean_roc_auc')
                std = metrics.get('cv_metric_std_roc_auc')
                print(f"ROC AUC (mean): {mean:.4f}")
                print(f"ROC AUC (std): {std:.4f}")
                if metrics.get('model_path'):
                    print(f"Saved model: {metrics.get('model_path')}")
            else:
                # Fallback: if older trainer returned arrays/lists of scores, print summary
                try:
                    import numpy as _np
                    for metric, scores in metrics.items():
                        arr = _np.array(scores)
                        print(f"{metric}: {arr.mean():.3f} (+/- {arr.std() * 2:.3f})")
                except Exception:
                    # Last-resort print
                    print(metrics)
        else:
            metrics = trainer.train_model(X, y)
            print('\nTraining complete:')
            print(metrics)
        
        sys.stdout.flush()
    except Exception as e:
        print(f"Unhandled error during retrain: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    main()
