from ast import Raise
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any
import uvicorn
from feature_extractor import URLFeatureExtractor
# Import download helper to optionally fetch model artifacts at startup
from scripts import download_models
from model_trainer import PhishingModelTrainer
import os

app = FastAPI(title="Phishing Prevention API")

# Allow local extension and localhost to call the API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
feature_extractor = URLFeatureExtractor()
model_trainer = PhishingModelTrainer()

# Small whitelist to avoid false positives for common trusted domains (local dev)
WHITELIST = {
    'youtube.com', 'google.com', 'gmail.com', 'facebook.com', 'twitter.com',
    'github.com', 'amazon.com', 'microsoft.com', 'linkedin.com'
}

# Prediction confidence threshold (below this -> treated as not phishing)
PHISHING_CONFIDENCE_THRESHOLD = 0.8

# Load the latest model
def load_latest_model():
    try:
        model_dir = 'models'
        logging.info(f"Looking for models in directory: {model_dir}")
        
        if not os.path.exists(model_dir):
            logging.error(f"Model directory {model_dir} not found")
            raise Exception("No trained model found - directory missing")
        
        models = [f for f in os.listdir(model_dir) if f.startswith('phishing_model_')]
        logging.info(f"Found model files: {models}")
        
        if not models:
            logging.error("No model files found in models directory")
            raise Exception("No trained model found - no model files")
        
        latest_model = sorted(models)[-1]
        latest_scaler = f"scaler_{latest_model.split('phishing_model_')[1]}"
        
        model_path = os.path.join(model_dir, latest_model)
        scaler_path = os.path.join(model_dir, latest_scaler)
        
        logging.info(f"Loading model from: {model_path}")
        logging.info(f"Loading scaler from: {scaler_path}")
        
        model_trainer.load_model(model_path, scaler_path)
        logging.info("Model and scaler loaded successfully")
    except Exception as e:
        logging.error(f"Error loading model: {str(e)}")
        Raise

# Load model on startup
@app.on_event("startup")
async def startup_event():
    try:
        logging.basicConfig(level=logging.DEBUG)
        logging.info("Starting up server...")
        # Attempt to download model artifacts if environment variables are configured
        try:
            download_models.download_models_if_missing()
        except Exception as e:
            logging.warning(f"Model download attempt failed: {e}")

        load_latest_model()
        logging.info("Server startup complete")
    except Exception as e:
        logging.error(f"Critical error loading model: {str(e)}", exc_info=True)
        raise  # This will prevent the app from starting if model loading fails

class URLCheckRequest(BaseModel):
    url: HttpUrl

class URLCheckResponse(BaseModel):
    is_phishing: bool
    confidence: float
    features: Dict[str, Any]
    risk_factors: list[str]

@app.post("/check-url", response_model=URLCheckResponse)
async def check_url(request_payload: URLCheckRequest, req: Request):
    try:
        # Enforce API key if configured in environment
        api_key_env = os.getenv('API_KEY')
        if api_key_env:
            client_key = req.headers.get('x-api-key') or req.headers.get('X-API-KEY')
            if not client_key or client_key != api_key_env:
                raise HTTPException(status_code=401, detail='Invalid or missing API key')
        # Extract features
        features = feature_extractor.extract_features(str(request_payload.url))
        if features is None:
            raise HTTPException(status_code=400, message="Could not extract features from URL")
        # Simple registered-domain helper
        from urllib.parse import urlparse
        parsed = urlparse(str(request_payload.url))
        host = (parsed.hostname or parsed.netloc or '').lower()
        host_parts = host.split('.') if host else []
        reg_domain = '.'.join(host_parts[-2:]) if len(host_parts) >= 2 else host

        # Check whitelist first
        if reg_domain in WHITELIST:
            return URLCheckResponse(is_phishing=False, confidence=0.0, features=features, risk_factors=['whitelisted'])

        # Get prediction
        prediction = model_trainer.predict(features)

        # Apply confidence threshold: only mark phishing when confidence exceeds threshold
        if prediction.get('confidence', 0.0) < PHISHING_CONFIDENCE_THRESHOLD:
            prediction['is_phishing'] = False
        
        # Analyze risk factors
        risk_factors = analyze_risk_factors(features)
        
        return URLCheckResponse(
            is_phishing=prediction['is_phishing'],
            confidence=prediction['confidence'],
            features=features,
            risk_factors=risk_factors
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def analyze_risk_factors(features: Dict[str, Any]) -> list[str]:
    """Analyze features to determine specific risk factors"""
    risk_factors = []
    
    # URL-based risks
    if features['url_features']['has_ip_address']:
        risk_factors.append("URL contains IP address instead of domain name")
    if features['url_features']['has_at_symbol']:
        risk_factors.append("URL contains @ symbol")
    if features['url_features']['has_double_slash']:
        risk_factors.append("URL path contains double slash")
    
    # Domain-based risks
    domain_age = features['domain_features'].get('domain_age', -1)
    has_whois = features['domain_features'].get('has_whois', False)
    if domain_age != -1 and domain_age < 30:
        risk_factors.append("Domain is less than 30 days old")
    if not has_whois and domain_age != -1:
        # Only report missing WHOIS when we attempted lookup (domain_age != -1)
        risk_factors.append("No WHOIS information available")
    
    # Content-based risks
    if features['content_features']['has_password_field'] and features['ssl_features']['has_ssl'] == False:
        risk_factors.append("Password field present without SSL")
    # Content-based risks: be robust to sentinel -1 values
    if features['content_features'].get('has_hidden_element'):
        risk_factors.append("Page contains hidden elements")
    num_iframes = features['content_features'].get('num_iframes', -1)
    if num_iframes != -1 and num_iframes > 0:
        risk_factors.append("Page contains iframes")
    
    # SSL-based risks
    if not features['ssl_features']['has_ssl']:
        risk_factors.append("No SSL certificate")
    elif features['ssl_features']['ssl_days_valid'] < 30:
        risk_factors.append("SSL certificate expires soon")
    
    return risk_factors

if __name__ == "__main__":
    # For local development on Windows, bind to localhost and avoid reload to prevent
    # occasional port binding / reload issues that surface as timeouts.
    uvicorn.run(
        app=app,
        host="127.0.0.1",
        port=8000,
        log_level="debug",
        use_colors=True,
        access_log=True
    )