document.getElementById('save').addEventListener('click', () => {
  const apiUrl = document.getElementById('apiUrl').value.trim();
  const apiKey = document.getElementById('apiKey').value.trim();
  chrome.storage.sync.set({ apiUrl, apiKey }, () => {
    document.getElementById('status').textContent = 'Saved.';
    setTimeout(() => document.getElementById('status').textContent = '', 2000);
  });
});

// Load existing
chrome.storage.sync.get(['apiUrl','apiKey'], (items) => {
  if (items.apiUrl) document.getElementById('apiUrl').value = items.apiUrl;
  if (items.apiKey) document.getElementById('apiKey').value = items.apiKey;
});
