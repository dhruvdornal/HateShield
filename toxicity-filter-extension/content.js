
// Configuration
let config = {
    enabled: true,
    apiEndpoint: 'https://ozymozy-toxi.hf.space/censor-post'
  };
  
  // Caching system
  const textCache = {};
  const CACHE_EXPIRY = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
  
  // Get settings from background script
  chrome.runtime.sendMessage({ action: "getSettings" }, (response) => {
    if (response) {
      config = response;
      console.log("Toxicity Filter initialized with settings:", config);
      
      // Load cache from storage
      loadCacheFromStorage().then(() => {
        startObserving();
      });
    }
  });
  
  // Load cache from chrome storage
  async function loadCacheFromStorage() {
    return new Promise((resolve) => {
      chrome.storage.local.get(['toxicityCache', 'cacheTimestamp'], (result) => {
        if (result.toxicityCache && result.cacheTimestamp) {
          // Check if cache is still valid (less than 24 hours old)
          const now = Date.now();
          if (now - result.cacheTimestamp < CACHE_EXPIRY) {
            Object.assign(textCache, result.toxicityCache);
            console.log(`Loaded ${Object.keys(textCache).length} items from cache`);
          } else {
            console.log("Cache expired, creating new cache");
            // Save a new empty cache with current timestamp
            saveCache();
          }
        } else {
          console.log("No cache found, creating new cache");
          saveCache();
        }
        resolve();
      });
    });
  }
  
  // Save cache to chrome storage
  function saveCache() {
    chrome.storage.local.set({
      toxicityCache: textCache,
      cacheTimestamp: Date.now()
    });
  }
  
  // Debounced version of saveCache to prevent excessive writes
  const debouncedSaveCache = debounce(() => {
    saveCache();
  }, 5000); // Save cache at most every 5 seconds
  
  // Function to check text with the API or get from cache
  async function checkToxicity(text) {
    // Create a shortened key for the cache to avoid huge strings
    // Use the first 50 chars + length as a reasonable unique identifier
    const textKey = `${text.substring(0, 50)}:${text.length}`;
    
    // Check cache first
    if (textCache[textKey]) {
      return textCache[textKey];
    }
    
    // If not in cache, call the API
    try {
      const response = await fetch(config.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: text })
      });
      
      const result = await response.json();
      
      // Cache the result
      textCache[textKey] = result;
      debouncedSaveCache();
      
      return result;
    } catch (error) {
      console.error("Error checking toxicity:", error);
      return { censored_text: text, has_profanity: false };
    }
  }
  
  // Function to process text nodes
  async function processPotentialToxicContent(element, platform) {
    // Skip if the element has already been processed
    if (element.dataset.toxicityProcessed === 'true') {
      return;
    }
    
    // Skip empty text or very short text
    const text = element.textContent.trim();
    if (!text || text.length < 3) {
      return;
    }
    
    // Skip if it's an input field or textarea
    if (element.isContentEditable || element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
      return;
    }
    
    // Mark as processed
    element.dataset.toxicityProcessed = 'true';
    
    // Check and censor if needed
    const result = await checkToxicity(text);
    if (result.has_profanity) {
      // For Instagram, we need to be extra careful with how we modify content
      if (platform === 'instagram') {
        // Instead of replacing the entire textContent, we'll preserve the element's structure
        // and replace only the text nodes within it
        replaceTextNodesCarefully(element, text, result.censored_text);
      } else {
        // For other platforms, we can use the simpler approach
        element.textContent = result.censored_text;
      }
      
      // Log for debugging
      console.log("Censored text:", text, "->", result.censored_text);
    }
  }
  
  // Function to carefully replace text nodes without disturbing element structure
  function replaceTextNodesCarefully(element, originalText, censoredText) {
    // If the element has no children, it's safe to replace the text directly
    if (element.childNodes.length === 0 || 
        (element.childNodes.length === 1 && element.childNodes[0].nodeType === Node.TEXT_NODE)) {
      element.textContent = censoredText;
      return;
    }
    
    // Otherwise, we need to find and replace only the text nodes
    const textNodes = [];
    const walk = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
    let node;
    while (node = walk.nextNode()) {
      textNodes.push(node);
    }
    
    // Replace each text node that contains toxic content
    textNodes.forEach(textNode => {
      if (textNode.textContent.trim() !== '') {
        const nodeText = textNode.textContent;
        // Check if this text node contains part of the toxic text
        if (originalText.includes(nodeText) || nodeText.includes(originalText)) {
          // Use cached result when possible
          checkToxicity(nodeText).then(result => {
            if (result.has_profanity) {
              textNode.textContent = result.censored_text;
            }
          });
        }
      }
    });
  }
  
  // Platform-specific selectors
  const platformSelectors = {
    x: {
      posts: 'article',
      textContainers: 'div[data-testid="tweetText"] span'
    },
    instagram: {
      posts: 'article, div[role="dialog"]',
      textContainers: '._a9zs, ._aacl, div[role="button"] span, div[dir="auto"], span[dir="auto"]'
    },
    threads: {
      posts: 'div[role="article"]',
      textContainers: 'span[data-pressable-container="true"], div[dir="auto"], span.x1lliihq, span.x1iorvi4, div.xdj266r'
    },
    reddit: {
      posts: 'h1[id^="post-title-"], div[id^="t3_"][id*="-post-rtjson-content"], div[id^="t1_"][id*="-comment-rtjson-content"]',
      textContainers: 'h1[id^="post-title-"], div[id^="t3_"][id*="-post-rtjson-content"] p, div[id^="t1_"][id*="-post-rtjson-content"] p'
    }
  };
  
  // Determine which platform we're on
  function getCurrentPlatform() {
    const host = window.location.hostname;
    if (host.includes('x.com')) return 'x';
    if (host.includes('instagram.com')) return 'instagram';
    if (host.includes('threads.net')) return 'threads';
    if (host.includes('reddit.com')) return 'reddit';
    return null;
  }
  
  // Store already processed elements to avoid repetitive work
  const processedElements = new WeakSet();
  
  // Process the current page
  async function processPage() {
    if (!config.enabled) return;
    
    const platform = getCurrentPlatform();
    if (!platform) return;
    
    const selectors = platformSelectors[platform];
    
    // Process existing content that hasn't been processed yet
    const elements = document.querySelectorAll(selectors.textContainers);
    
    // Create an array of elements that haven't been processed
    const unprocessedElements = Array.from(elements).filter(el => !processedElements.has(el));
    
    if (unprocessedElements.length > 0) {
      console.log(`Processing ${unprocessedElements.length} new text elements on ${platform}`);
    }
    
    unprocessedElements.forEach(element => {
      processedElements.add(element);
      processPotentialToxicContent(element, platform);
    });
    
    // Platform-specific additional processing
    if (platform === 'instagram') {
      // For Instagram, also check for dynamic content in comments
      document.querySelectorAll('div[role="menuitem"], div[data-visualcompletion="ignore-dynamic"]')
        .forEach(element => {
          if (!processedElements.has(element) && element.textContent.trim().length > 3) {
            processedElements.add(element);
            processPotentialToxicContent(element, platform);
          }
      });
    } else if (platform === 'threads') {
      // For Threads.net, also try a more general approach
      const possibleComments = document.querySelectorAll('span, div[dir="auto"]');
      possibleComments.forEach(element => {
        // If the element contains text and isn't too short, process it
        if (!processedElements.has(element) && element.textContent.trim().length > 3) {
          processedElements.add(element);
          processPotentialToxicContent(element, platform);
        }
      });
    }
  }
  
  // Optimized observer setup - batch processing with requestAnimationFrame
  let pendingMutations = false;
  
  // MutationObserver to detect new content
  function startObserving() {
    // Process the page initially
    requestAnimationFrame(() => {
      processPage();
    });
    
    // Set up the observer with batch processing
    const observer = new MutationObserver((mutations) => {
      if (!config.enabled || pendingMutations) return;
      
      pendingMutations = true;
      
      // Use requestAnimationFrame to batch multiple mutations together
      requestAnimationFrame(() => {
        processPage();
        pendingMutations = false;
      });
    });
    
    // Start observing the document with the configured parameters
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    // Optimize event handlers with throttling
    const throttledProcessPage = throttle(() => {
      requestAnimationFrame(() => {
        processPage();
      });
    }, 1000); // Process at most once per second for scroll/click events
    
    // For dynamic content loading platforms
    window.addEventListener('scroll', throttledProcessPage);
    window.addEventListener('click', throttledProcessPage);
  }
  
  // Helper function to throttle events
  function throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    }
  }
  
  // Helper function to debounce events
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
  
  // Listen for settings updates from popup
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "settingsUpdated") {
      config = request.settings;
      console.log("Settings updated:", config);
    }
  });
  
  // Inject a style to hide the temporary flicker that might occur during content replacement
  function injectStyles() {
    const styleElement = document.createElement('style');
    styleElement.textContent = `
      [data-toxicity-processed="true"] {
        transition: opacity 0.1s ease-in-out;
      }
    `;
    document.head.appendChild(styleElement);
  }
  
  // Initialize styles
  injectStyles();