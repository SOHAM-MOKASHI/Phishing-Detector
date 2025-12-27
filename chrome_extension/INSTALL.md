Phishing Detector — Installation Guide

This guide explains how to install the Chrome extension and run the local API so non-technical users can use the extension on desktop and Android (Kiwi). It also includes quick troubleshooting.

Prerequisites (for each user)
- Chrome or Edge on desktop (Windows/Mac/Linux) OR Firefox (desktop) OR Kiwi Browser (Android).
- If using locally: Python 3.8+ and the project cloned locally.
- If using a hosted API: the extension must be configured to point at the hosted HTTPS API URL.

1) Running the API locally (required for local-only use)
- Open PowerShell (Windows) or terminal (Mac/Linux).
- From the project root run:

```powershell
# Windows (PowerShell)
C:/Users/Soham/OneDrive/Documents/python/app.1/.venv/Scripts/python.exe src/app.py

# or using the virtualenv python directly after activating the venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python src/app.py
```

- The API will listen on `http://127.0.0.1:8000` by default.

2) Desktop installation (Chrome / Edge)
- Open Chrome (or Edge) and navigate to `chrome://extensions/`.
- Enable "Developer mode" (top-right).
- Click "Load unpacked" and choose the `chrome_extension` folder from the repository.
- The extension icon will appear in the toolbar. Visit any website, click the icon and press "Check current page".

Notes:
- The extension expects the API at `http://127.0.0.1:8000/check-url` by default. If you host the API elsewhere, see section "Change extension API URL" below.
- If the popup shows "Failed to contact API", confirm the API server is running on the same machine.

3) Desktop installation (Firefox for Desktop)
- Firefox uses a different extension format. For testing you can load the extension temporarily:
  - Open `about:debugging#/runtime/this-firefox` -> "Load Temporary Add-on..."
  - Choose `chrome_extension/manifest.json` (Firefox accepts many WebExtension manifest fields).
- For public distribution, publish to Mozilla Add-ons (AMO).

4) Android (Kiwi Browser)
- Install Kiwi Browser from Google Play.
- Open Kiwi and go to `chrome://extensions/` (or open the Extensions menu in Kiwi).
- Enable Developer mode (toggle) and click "Load unpacked" or add the packed `.zip`/`.crx` if Kiwi supports it.
- IMPORTANT: The API must be reachable from the phone. Options:
  - Run the API on a machine and expose it via a tunnel (ngrok) and update the extension API URL to the ngrok HTTPS URL.
  - Or host the API on a public HTTPS host and update the extension API URL.

5) Change extension API URL (if using hosted API or ngrok)
- Open `chrome_extension/popup.js` and `chrome_extension/background.js` and replace the local URL `http://127.0.0.1:8000/check-url` with the public HTTPS base `https://your-host.example.com/check-url`.
- Save files and reload the extension in `chrome://extensions`.

6) Packing the extension for distribution (zip)
- Zip the contents of the `chrome_extension` folder (do NOT include server/model files).
- Distribute the zip to users with these instructions:
  - Desktop: they can unpack and load the unpacked extension (developer mode) or install the packed CRX if their browser allows it.
  - Kiwi (Android): Kiwi supports loading CRX or zip in its extension interface.

7) Publishing to stores (optional)
- Chrome Web Store: requires a one-time $5 developer registration fee. Upload the packed zip there.
- Mozilla AMO: free; upload the extension and follow the review process.

8) Troubleshooting
- Popup says "Failed to contact API": check that `src/app.py` is running and reachable on `127.0.0.1:8000` (or the configured URL).
- Extension shows JSON instead of text: Reload the extension (we updated `popup.js` to show plain text). If you see raw JSON, ensure you loaded the updated `popup.js` (reload extension).
- Content script banner not appearing: Ensure `content_script.js` is running on that page (some internal pages `chrome://` or `about:` cannot be accessed).

9) Security & privacy
- If you host the API publicly, secure it via HTTPS and require a token. Restrict CORS to only your extension origin.
- Do not publish model files or datasets with private data in the extension package.

If you'd like, I can also:
- Create a zipped package of the `chrome_extension` folder for you to download, or
- Provide a short one-page PDF with the above steps for non-technical users.

Contact me which of those (zip/pdf) you'd like and I will prepare it.
