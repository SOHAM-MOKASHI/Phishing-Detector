import pandas as pd
from feature_extractor import URLFeatureExtractor
from model_trainer import PhishingModelTrainer

def main():
    # Load your dataset of URLs and their labels
    # Format should be: DataFrame with 'url' and 'is_phishing' columns
    dataset = pd.read_csv('dataset.csv')
    
    # Extract features
    extractor = URLFeatureExtractor()
    features = []
    labels = []
    
    print("Extracting features from URLs...")
    for index, row in dataset.iterrows():
        url_features = extractor.extract_features(row['url'])
        if url_features is not None:
            features.append(url_features)
            labels.append(row['is_phishing'])
        
        if index % 100 == 0:
            print(f"Processed {index} URLs...")
    
    # Convert features to DataFrame and flatten
    features_df = pd.DataFrame(features)
    trainer = PhishingModelTrainer()
    features_prepared = trainer.prepare_data(features_df)
    labels = pd.Series(labels)

    # Train the model
    print("Training model...")
    metrics = trainer.train_model(features_prepared, labels)
    
    print("\nTraining completed!")
    print(f"Train accuracy: {metrics['train_accuracy']:.4f}")
    print(f"Test accuracy: {metrics['test_accuracy']:.4f}")
    print(f"Model saved to: {metrics['model_path']}")

if __name__ == "__main__":
    main()