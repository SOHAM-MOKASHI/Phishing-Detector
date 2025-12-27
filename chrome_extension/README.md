# Phishing Checker Chrome Extension

This Chrome extension sends the current tab URL to your local Phishing Prevention API (`/check-url`) and displays the model's prediction.

## Install (Developer mode)
1. Ensure your API server is running locally: from your project root run:

```powershell
C:/Users/Soham/OneDrive/Documents/python/app.1/.venv/Scripts/python.exe src/app.py
```

The API listens on `http://127.0.0.1:8000` by default.

2. Load the extension in Chrome/Edge:
- Open `chrome://extensions/`
- Enable `Developer mode` (top-right)
- Click `Load unpacked` and select the `chrome_extension` folder in the project root.

3. Click the extension icon and press `Check current page`.

## Troubleshooting
- If you see "Failed to contact API", ensure `src/app.py` is running and reachable at `http://127.0.0.1:8000/check-url`.
- If the extension shows `No active tab URL available`, make sure a tab is active and not a Chrome internal page (extensions cannot access `chrome://` URLs).

## Next steps (optional)
- Add a content script to auto-scan pages and set a badge color when phishing is detected.
- Add OAuth or secure local socket if exposing API on a network.
 
## Auto-scan and badge
The extension now includes a background service worker and a content script that automatically checks pages and sets a badge when suspicious:

- `background.js` — service worker that queries `http://127.0.0.1:8000/check-url` and sets the extension badge text to `PH` when phishing is detected.
- `content_script.js` — requests a check when pages load and displays a small in-page banner if the page is flagged.

If you prefer to disable auto-scanning, remove the `content_scripts` entry from `chrome_extension/manifest.json` and reload the extension.
