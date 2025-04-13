// When popup loads, get current settings
document.addEventListener('DOMContentLoaded', () => {
    chrome.storage.local.get(['enabled', 'apiEndpoint', 'toxicityCache', 'cacheTimestamp'], (result) => {
      document.getElementById('enable-toggle').checked = result.enabled;
      document.getElementById('api-endpoint').value = result.apiEndpoint || 'https://ozymozy-toxi.hf.space/censor-post';
      updateStatusText(result.enabled);
      
      // Update cache information
      updateCacheInfo(result.toxicityCache, result.cacheTimestamp);
    });
    
    // Save button click handler
    document.getElementById('save-btn').addEventListener('click', () => {
      const enabled = document.getElementById('enable-toggle').checked;
      const apiEndpoint = document.getElementById('api-endpoint').value;
      
      // Save settings
      chrome.storage.local.set({ enabled, apiEndpoint }, () => {
        updateStatusText(enabled);
        
        // Notify content scripts that settings have changed
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, { 
              action: "settingsUpdated", 
              settings: { enabled, apiEndpoint } 
            });
          }
        });
        
        // Show saved notification
        const saveBtn = document.getElementById('save-btn');
        saveBtn.textContent = 'Saved!';
        setTimeout(() => {
          saveBtn.textContent = 'Save Settings';
        }, 1500);
      });
    });
    
    // Clear cache button handler
    document.getElementById('clear-cache-btn').addEventListener('click', () => {
      chrome.runtime.sendMessage({ action: "clearCache" }, (response) => {
        if (response && response.success) {
          // Update cache information after clearing
          updateCacheInfo({}, Date.now());
          
          // Show cleared notification
          const clearBtn = document.getElementById('clear-cache-btn');
          clearBtn.textContent = 'Cache Cleared!';
          setTimeout(() => {
            clearBtn.textContent = 'Clear Cache';
          }, 1500);
        }
      });
    });
    
    // Toggle switch handler
    document.getElementById('enable-toggle').addEventListener('change', (e) => {
      updateStatusText(e.target.checked);
    });
  });
  
  // Update status text
  function updateStatusText(enabled) {
    const statusText = document.getElementById('status-text');
    statusText.textContent = enabled ? 'enabled' : 'disabled';
    statusText.style.color = enabled ? '#4CAF50' : '#F44336';
  }
  
  // Update cache information
  function updateCacheInfo(cache, timestamp) {
    const cacheInfo = document.getElementById('cache-info');
    const cacheItems = cache ? Object.keys(cache).length : 0;
    const lastUpdated = new Date(timestamp).toLocaleString();
    
    cacheInfo.textContent = `Cache contains ${cacheItems} items. Last updated: ${lastUpdated}`;
  }