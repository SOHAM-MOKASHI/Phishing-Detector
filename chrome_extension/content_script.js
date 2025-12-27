// Content script: asks background to check the current page and optionally shows an overlay

// Request a check when the page loads
chrome.runtime.sendMessage({ action: 'check_url', url: window.location.href }, (resp) => {
  // we don't need to do anything here; background will set badge and can send result back
});

// Receive check results from background and show an in-page banner for phishing
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.action !== 'check_result') return;
  const result = message.result;
  if (!result || result.error) return;
  if (result.is_phishing) {
    showBanner(result);
  }
});

function showBanner(result) {
  try {
    if (document.getElementById('__phish_banner')) return; // already present
    const banner = document.createElement('div');
    banner.id = '__phish_banner';
    banner.style.position = 'fixed';
    banner.style.top = '0';
    banner.style.left = '0';
    banner.style.right = '0';
    banner.style.zIndex = '2147483647';
    banner.style.background = '#d32f2f';
    banner.style.color = 'white';
    banner.style.padding = '8px 12px';
    banner.style.fontFamily = 'Arial, sans-serif';
    banner.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    banner.textContent = 'Warning: This page looks suspicious (phishing suspected). Click extension for details.';
    banner.addEventListener('click', () => banner.remove());
    document.body.appendChild(banner);
  } catch (e) {
    // ignore
  }
}
