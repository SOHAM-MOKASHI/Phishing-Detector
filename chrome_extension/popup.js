async function getActiveTabUrl() {
  return new Promise((resolve) => {
    try {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (!tabs || tabs.length === 0) return resolve(null);
        resolve(tabs[0].url);
      });
    } catch (e) {
      resolve(null);
    }
  });
}

async function getSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['apiUrl','apiKey'], (items) => {
      resolve({ apiUrl: items.apiUrl || 'http://127.0.0.1:8000/check-url', apiKey: items.apiKey || '' });
    });
  });
}

async function checkUrl(url) {
  const settings = await getSettings();
  const apiUrl = settings.apiUrl;
  const apiKey = settings.apiKey;
  try {
    const headers = { 'Content-Type': 'application/json' };
    if (apiKey) headers['x-api-key'] = apiKey;
    const r = await fetch(apiUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify({ url })
    });
    if (!r.ok) {
      const t = await r.text();
      throw new Error(`${r.status} ${t}`);
    }
    return await r.json();
  } catch (e) {
    throw e;
  }
}

document.getElementById('checkBtn').addEventListener('click', async () => {
  const status = document.getElementById('status');
  const result = document.getElementById('result');
  status.textContent = 'Retrieving active tab...';
  result.textContent = '';

  const url = await getActiveTabUrl();
  if (!url) {
    status.textContent = 'No active tab URL available';
    return;
  }

  status.textContent = `Checking ${url}`;
  try {
    const data = await checkUrl(url);
    // Build plain text summary
    const lines = [];
    lines.push(`Result: ${data.is_phishing ? 'Phishing' : 'Likely legitimate'}`);
    lines.push(`Confidence: ${data.confidence}`);
    if (data.risk_factors && data.risk_factors.length) {
      lines.push('Risk factors:');
      for (const rf of data.risk_factors) lines.push(`- ${rf}`);
    }
    lines.push('');
    lines.push('Key features:');
    // Show some high-level features in plain text
    const f = data.features || {};
    if (f.url_length !== undefined) lines.push(`- URL length: ${f.url_length}`);
    const df = f.domain_features || {};
    lines.push(`- Domain age: ${df.domain_age}`);
    lines.push(`- Has WHOIS: ${df.has_whois}`);
    const uf = f.url_features || {};
    lines.push(`- Dots: ${uf.num_dots}, Digits: ${uf.num_digits}, Special chars: ${uf.num_special_chars}`);
    const cf = f.content_features || {};
    lines.push(`- External links: ${cf.num_external_links}, Iframes: ${cf.num_iframes}, Hidden elements: ${cf.has_hidden_element}`);

    result.textContent = lines.join('\n');
    status.textContent = data.is_phishing ? 'Phishing detected' : 'Likely legitimate';
  } catch (e) {
    result.textContent = `Error: ${e}`;
    status.textContent = 'Failed to contact API';
  }
});
