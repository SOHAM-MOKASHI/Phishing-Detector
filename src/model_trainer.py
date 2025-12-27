import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import joblib
from datetime import datetime
import os

class PhishingModelTrainer:
    def __init__(self, model_path='models'):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        os.makedirs(model_path, exist_ok=True)

    def prepare_data(self, features_df):
        """Prepare and preprocess the feature data"""
        # Flatten nested dictionary features
        flat_data = []
        for _, row in features_df.iterrows():
            flat_row = {}
            for key, value in row.items():
                if isinstance(value, dict):
                    flat_row.update({f"{key}_{k}": v for k, v in value.items()})
                else:
                    flat_row[key] = value
            flat_data.append(flat_row)
        df = pd.DataFrame(flat_data)
        # Keep only numeric columns for ML
        df = df.select_dtypes(include=["number"])
        return df

    def train_model(self, X, y, class_weight=None, cv=None):
        """Train the Random Forest model.

        Parameters:
        - X: feature matrix (DataFrame or ndarray)
        - y: labels (Series or ndarray)
        - class_weight: passed to RandomForestClassifier (e.g., 'balanced' or dict)
        - cv: if provided (int), run StratifiedKFold CV with `cv` folds and return CV metrics
        """
        from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
        from sklearn.metrics import accuracy_score

        # Convert to numpy if pandas
        X_in = X
        y_in = y

        if cv and int(cv) > 1:
            # Cross-validation path
            clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight=class_weight, n_jobs=-1)
            skf = StratifiedKFold(n_splits=int(cv), shuffle=True, random_state=42)
            scores = cross_val_score(clf, X_in, y_in, cv=skf, scoring='roc_auc', n_jobs=-1)
            # Fit final model on full data
            self.scaler.fit(X_in)
            X_scaled = self.scaler.transform(X_in)
            self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight=class_weight, n_jobs=-1)
            self.model.fit(X_scaled, y_in)

            # Save artifacts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_filename = f"phishing_model_{timestamp}.joblib"
            scaler_filename = f"scaler_{timestamp}.joblib"
            joblib.dump(self.model, os.path.join(self.model_path, model_filename))
            joblib.dump(self.scaler, os.path.join(self.model_path, scaler_filename))

            return {
                'cv_metric_mean_roc_auc': float(scores.mean()),
                'cv_metric_std_roc_auc': float(scores.std()),
                'model_path': os.path.join(self.model_path, model_filename)
            }

        # Default train/test split path
        X_train, X_test, y_train, y_test = train_test_split(X_in, y_in, test_size=0.2, random_state=42, stratify=y_in)

        # Scale the features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train Random Forest model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight=class_weight,
            n_jobs=-1
        )
        self.model.fit(X_train_scaled, y_train)

        # Save the model and scaler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"phishing_model_{timestamp}.joblib"
        scaler_filename = f"scaler_{timestamp}.joblib"

        joblib.dump(self.model, os.path.join(self.model_path, model_filename))
        joblib.dump(self.scaler, os.path.join(self.model_path, scaler_filename))

        # Calculate and return metrics
        train_score = accuracy_score(y_train, self.model.predict(X_train_scaled))
        test_score = accuracy_score(y_test, self.model.predict(X_test_scaled))

        return {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'model_path': os.path.join(self.model_path, model_filename)
        }

    def load_model(self, model_path, scaler_path):
        """Load a trained model and scaler"""
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)

    def predict(self, features):
        """Make predictions using the trained model"""
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Prepare features
        features_df = pd.DataFrame([features])
        features_prepared = self.prepare_data(features_df)
        # Align features to scaler's expected feature names (if available)
        try:
            expected = getattr(self.scaler, 'feature_names_in_', None)
            if expected is not None:
                expected = list(expected)
                # Add any missing expected columns with zeros
                for col in expected:
                    if col not in features_prepared.columns:
                        features_prepared[col] = 0
                # Drop any columns that were not present during fit
                features_prepared = features_prepared.reindex(columns=expected)
            else:
                # If scaler has no feature names, try to ensure correct number of features
                expected_n = getattr(self.model, 'n_features_in_', None)
                if expected_n is not None and features_prepared.shape[1] != expected_n:
                    # If fewer features, pad with zeros; if more, truncate to the expected count
                    if features_prepared.shape[1] < expected_n:
                        for i in range(expected_n - features_prepared.shape[1]):
                            features_prepared[f'_pad_{i}'] = 0
                    else:
                        features_prepared = features_prepared.iloc[:, :expected_n]

            features_scaled = self.scaler.transform(features_prepared)
        except Exception as e:
            # Provide a clearer error message for feature mismatch
            raise ValueError(f"Feature alignment failed before transform: {e}")
        
        # Get prediction and probability
        prediction = self.model.predict(features_scaled)[0]
        probability = self.model.predict_proba(features_scaled)[0]
        
        return {
            'is_phishing': bool(prediction),
            'confidence': float(max(probability))
        }