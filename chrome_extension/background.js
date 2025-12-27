// Background service worker: listens for checks and tab changes, queries local API,
// sets the extension badge and forwards results to the page when applicable.

const API_BASE = 'http://127.0.0.1:8000/check-url';

async function fetchCheck(url) {
  try {
    const resp = await fetch(API_BASE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    if (!resp.ok) {
      const txt = await resp.text();
      return { error: `${resp.status} ${txt}` };
    }
    return await resp.json();
  } catch (e) {
    return { error: String(e) };
  }
}

function updateBadge(tabId, isPhish) {
  if (isPhish) {
    chrome.action.setBadgeText({ text: 'PH', tabId });
    chrome.action.setBadgeBackgroundColor({ color: '#d32f2f', tabId });
  } else {
    chrome.action.setBadgeText({ text: '', tabId });
  }
}

// Handle explicit requests from popup/content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.action !== 'check_url') return;
  const url = message.url;
  (async () => {
    const result = await fetchCheck(url);
    // Set badge on the sender tab if available
    const tabId = sender.tab ? sender.tab.id : (message.tabId || null);
    if (tabId && result && !result.error) updateBadge(tabId, result.is_phishing);
    sendResponse(result);
  })();
  return true; // will respond asynchronously
});

// Auto-check on tab activation
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    if (!tab || !tab.url) return;
    if (tab.url.startsWith('http')) {
      const result = await fetchCheck(tab.url);
      if (!result.error) updateBadge(activeInfo.tabId, result.is_phishing);
      // notify content script
      chrome.tabs.sendMessage(activeInfo.tabId, { action: 'check_result', result });
    }
  } catch (e) {
    // ignore
  }
});

// Auto-check on tab update (complete)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab && tab.url && tab.url.startsWith('http')) {
    (async () => {
      const result = await fetchCheck(tab.url);
      if (!result.error) updateBadge(tabId, result.is_phishing);
      chrome.tabs.sendMessage(tabId, { action: 'check_result', result });
    })();
  }
});
