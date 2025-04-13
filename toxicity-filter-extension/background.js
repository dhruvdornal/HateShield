// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
    // Set default settings
    chrome.storage.local.set({
      enabled: true,
      apiEndpoint: 'https://ozymozy-toxi.hf.space/censor-post'
    });
    
    // Initialize empty cache
    chrome.storage.local.set({
      toxicityCache: {},
      cacheTimestamp: Date.now()
    });
    
    console.log("Toxicity Filter extension installed. Cache initialized.");
  });
  
  // Listen for messages from content script or popup
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getSettings") {
      chrome.storage.local.get(['enabled', 'apiEndpoint'], (result) => {
        sendResponse(result);
      });
      return true; // Required for async response
    }
    
    if (request.action === "clearCache") {
      chrome.storage.local.set({
        toxicityCache: {},
        cacheTimestamp: Date.now()
      }, () => {
        sendResponse({ success: true, message: "Cache cleared successfully" });
      });
      return true;
    }
  });