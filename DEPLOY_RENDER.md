Deploying Phishing Detector to Render (quick guide)

1) Create a Render account
- Sign up at https://render.com and connect your GitHub account.

2) Create a new Web Service
- Click "New" -> "Web Service" -> Connect repository -> select `Phishing-Detector` (your repo).
- Branch: `main` (or whichever branch you pushed).
- Environment: Python 3 (the Dockerfile in repo will be used if you pick "Docker").

3) Build & Start commands
- If using the Dockerfile (recommended): choose "Docker" and Render will build using `Dockerfile`.
- If using "Native" (no Docker): Build Command: `pip install -r requirements.txt` ; Start Command: `uvicorn src.app:app --host 0.0.0.0 --port $PORT`

4) Environment variables (set in Render dashboard -> Environment -> Environment Variables)
- `API_KEY` : set to a secure random token (this will require extension to send `x-api-key` header).
- `MODEL_BASE_URL` : (optional) base HTTPS URL where model files are hosted (e.g., https://my-bucket.s3.amazonaws.com/models)
- `MODEL_FILES` : (optional) comma-separated filenames to download (e.g., phishing_model_20251208_145109.joblib,scaler_20251208_145109.joblib)

5) Models
- Upload `models/*.joblib` to the deployed instance manually (not recommended) OR
- Upload model files to an object store (S3/DigitalOcean Spaces) and set `MODEL_BASE_URL` and `MODEL_FILES` so the server downloads them at startup. Ensure objects are publicly readable or use signed URLs and adapt `scripts/download_models.py` to use signed links.

6) Secure the API
- The app enforces `x-api-key` header when `API_KEY` is set. When configuring the extension, set the same API key in Options.
- Use HTTPS (Render provides it automatically for your service).

7) Test
- After deployment, visit the service URL (e.g., https://my-phish-api.onrender.com). Test by POSTing:

  curl -X POST 'https://<your-domain>/check-url' -H 'Content-Type: application/json' -H 'x-api-key: <your-key>' -d '{"url":"https://example.com"}'

8) Update extension
- In extension Options set API URL to `https://<your-domain>/check-url` and API Key to your `API_KEY` value.

9) Notes
- Monitor logs in the Render dashboard for download errors or model loading errors.
- If the download helper fails (network/permissions), upload models to the instance or S3 and verify access.

*** End of guide
