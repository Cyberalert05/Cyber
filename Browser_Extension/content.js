// CODAR Shield — Content Script v2.2 (Restored Original Logic + Fixes)
// Multi-platform toxicity scanner with surgical blur.
// Supports: Twitter/X, YouTube, Instagram, WhatsApp Web, Facebook, and any generic page.

(function () {
    'use strict';

    // ==================== ERROR HANDLING & CONTEXT CHECKS ====================
    
    // Check if the extension context is still valid
    function isOrphaned() {
        return typeof chrome === 'undefined' || !chrome.runtime || !chrome.runtime.id;
    }

    // Safe message sender to avoid "Extension context invalidated"
    function safeSendMessage(message, callback) {
        if (isOrphaned()) return;
        try {
            chrome.runtime.sendMessage(message, (response) => {
                if (chrome.runtime.lastError) return;
                if (callback) callback(response);
            });
        } catch (e) {
            console.warn('[CODAR Shield] Context invalidated.');
        }
    }

    // ==================== PLATFORM DETECTION ====================

    const PLATFORM_CONFIG = {
        twitter: {
            match: /^https?:\/\/(www\.)?(twitter\.com|x\.com)/i,
            name: 'Twitter / X',
            icon: '𝕏',
            selectors: [
                '[data-testid="tweetText"]',
                '[data-testid="tweet"] [lang]',
                '[data-testid="DmScrollerContainer"] [dir="auto"]',
                'article [dir="auto"]',
                '[data-testid="tweetPhoto"]',
                '[data-testid="videoPlayer"]',
                '[data-testid="videoComponent"]',
                '[data-testid="card.wrapper"]'
            ],
            excludeSelectors: [
                '[data-testid="UserName"]',
                'nav', 'header', '[role="banner"]',
                'a[href*="/status/"]'
            ]
        },
        youtube: {
            match: /^https?:\/\/(www\.)?youtube\.com/i,
            name: 'YouTube',
            icon: '▶',
            selectors: [
                'ytd-comment-renderer #content-text',
                '#content-text.ytd-comment-renderer',
                'ytd-comment-renderer .yt-core-attributed-string',
                '#comment #content-text',
                '#content-text',
                'yt-formatted-string.ytd-comment-renderer',
                '#description-inline-expander .yt-core-attributed-string',
                'ytd-live-chat-text-message-renderer #message'
            ],
            excludeSelectors: [
                '#owner', '#channel-name', '#video-title', 'ytd-topbar-logo-renderer',
                'tp-yt-paper-tab', '#tabs-inner-container'
            ]
        },
        instagram: {
            match: /^https?:\/\/(www\.)?instagram\.com/i,
            name: 'Instagram',
            icon: '📷',
            selectors: [
                'div._ap33', 'div._ap3a', 'span._ap3a', // Modern IG classes
                'article span[dir="auto"]',
                'ul li span[dir="auto"]',
                'div[role="dialog"] span[dir="auto"]',
                'div[role="row"] span[dir="auto"]',
                'div[role="listbox"] span[dir="auto"]',
                'section span[dir="auto"]',
                'main span[dir="auto"]'
            ],
            excludeSelectors: [
                'header', 'nav',
                'a[role="link"] span',
                'time', 'button span',
                'div[role="menuitem"]'
            ]
        },
        whatsapp: {
            match: /^https?:\/\/web\.whatsapp\.com/i,
            name: 'WhatsApp Web',
            icon: '💬',
            selectors: [
                'div.copyable-text span.selectable-text',
                'span.selectable-text.copyable-text',
                'div._akbu span', 'div._amk4 span', // Modern WA classes
                '.message-in .copyable-text span.selectable-text',
                '.message-out .copyable-text span.selectable-text',
                '.message-in span[dir="ltr"]',
                '.message-out span[dir="ltr"]',
                'div[data-pre-plain-text] span.selectable-text'
            ],
            excludeSelectors: [
                'header', '._1BOF7',
                'span[data-testid="conversation-info-header-chat-title"]',
                'div[data-testid="cell-frame-title"]',
                'footer'
            ]
        },
        facebook: {
            match: /^https?:\/\/(www\.)?(facebook\.com|fb\.com)/i,
            name: 'Facebook',
            icon: 'f',
            selectors: [
                'div[data-ad-preview="message"]',
                'div[dir="auto"][style*="text-align"]',
                'ul[role="list"] div[dir="auto"]',
                'div[aria-label*="Comment"] div[dir="auto"]',
                'div[role="row"] div[dir="auto"]',
                'div[class*="userContent"]',
                'div[data-ad-comet-preview="message"]',
                'span[dir="auto"]'
            ],
            excludeSelectors: [
                'a[role="link"]', 'h2', 'h3', 'nav',
                '[role="banner"]', '[role="navigation"]',
                'span[dir="auto"] a'
            ]
        }
    };

    function detectPlatform() {
        const url = window.location.href;
        for (const [key, config] of Object.entries(PLATFORM_CONFIG)) {
            if (config.match.test(url)) {
                return { key, ...config };
            }
        }
        return { key: 'generic', name: 'Website', icon: '🌐', selectors: [], excludeSelectors: [] };
    }

    const CURRENT_PLATFORM = detectPlatform();
    console.log(`[CODAR Shield] Platform detected: ${CURRENT_PLATFORM.name}`);

    // ==================== TOXICITY CLASSIFIER ====================

    const TOXIC_KEYWORDS = {
        high: [
            'kill yourself', 'kys', 'go die', 'hope you die', 'neck yourself',
            'stfu', 'shut the fuck up', 'piece of shit', 'worthless',
            'retard', 'retarded', 'faggot', 'fag', 'nigger', 'nigga',
            'whore', 'slut', 'bitch', 'cunt', 'dickhead', 'asshole',
            'hate you', 'kill you', 'rape', 'rapist', 'terrorist',
            'shoot up', 'bomb threat', 'gonna hurt you', 'watch your back',
            'fuk', 'fuck', 'f*ck', 'motherfucker', 'bastard', 'piss off',
            'scum', 'scumbag', 'degenerate', 'trash human', 'unalive',
            'low life', 'no life', 'kill urself', 'kill u', 'murder', 'die'
        ],
        medium: [
            'stupid', 'idiot', 'dumb', 'moron', 'loser', 'ugly',
            'fat', 'disgusting', 'pathetic', 'trash', 'garbage',
            'shut up', 'nobody likes you', 'no one cares', 'go away',
            'you suck', 'worst', 'terrible', 'awful', 'nasty',
            'creep', 'weirdo', 'freak', 'lame', 'useless', 'toxic',
            'stink', 'annoying', 'cringe', 'embarrassing', 'clown',
            'liar', 'fake', 'snake', 'coward', 'weak', 'horrible',
            'hate', 'hate speech', 'bully', 'harass', 'annoy'
        ]
    };

    function classifyText(text) {
        if (!text || text.trim().length < 5) return null;
        const lower = text.toLowerCase();

        for (const kw of TOXIC_KEYWORDS.high) {
            if (lower.includes(kw)) {
                return { level: 'toxic', score: 0.95, keyword: kw };
            }
        }

        let mediumCount = 0;
        let matchedKeyword = '';
        for (const kw of TOXIC_KEYWORDS.medium) {
            if (lower.includes(kw)) {
                mediumCount++;
                if (!matchedKeyword) matchedKeyword = kw;
            }
        }

        if (mediumCount >= 3) {
            return { level: 'toxic', score: 0.85, keyword: matchedKeyword };
        } else if (mediumCount >= 1) {
            return { level: 'warning', score: 0.5 + (mediumCount * 0.1), keyword: matchedKeyword };
        }

        // ALL CAPS aggression
        const letters = text.replace(/[^a-zA-Z]/g, '');
        if (letters.length > 15) {
            const capsRatio = text.replace(/[^A-Z]/g, '').length / letters.length;
            const exclCount = (text.match(/!/g) || []).length;
            if (capsRatio > 0.7 && exclCount >= 2) {
                return { level: 'warning', score: 0.45, keyword: 'AGGRESSIVE_TONE' };
            }
        }

        return null;
    }

    // ==================== SURGICAL DOM SCANNING ====================
    let scannedCount = 0;
    let flaggedCount = 0;
    let reportedCount = 0;

    const processedElements = new WeakSet();
    const processedTextNodes = new WeakSet();

    function isExcluded(element) {
        if (!element) return true;
        const excludes = CURRENT_PLATFORM.excludeSelectors || [];
        for (const sel of excludes) {
            try {
                if (element.matches && element.matches(sel)) return true;
                if (element.closest && element.closest(sel)) return true;
            } catch (e) { }
        }
        return false;
    }

    function getPlatformTextElements() {
        const results = [];
        if (CURRENT_PLATFORM.selectors.length > 0) {
            for (const selector of CURRENT_PLATFORM.selectors) {
                try {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        if (processedElements.has(el)) return;
                        if (isExcluded(el)) return;
                        const text = (el.innerText || el.textContent || '').trim();
                        if (text.length < 5 || text.length > 5000) return;
                        results.push({ text, element: el });
                    });
                } catch (e) { }
            }
        }
        const genericResults = getGenericTextElements();
        const seen = new Set(results.map(r => r.element));
        for (const gr of genericResults) {
            if (!seen.has(gr.element)) results.push(gr);
        }
        return results;
    }

    function getGenericTextElements() {
        const results = [];
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: function (node) {
                    if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
                    const parent = node.parentElement;
                    if (!parent) return NodeFilter.FILTER_REJECT;
                    const tag = parent.tagName.toLowerCase();
                    if (['script', 'style', 'noscript', 'textarea', 'input', 'code', 'pre'].includes(tag)) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    if (parent.classList && parent.classList.contains('codar-shield-wrap')) return NodeFilter.FILTER_REJECT;
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );

        let node;
        while ((node = walker.nextNode())) {
            if (processedTextNodes.has(node)) continue;
            const text = node.nodeValue.trim();
            if (text.length < 5 || text.length > 2000) continue;
            if (isExcluded(node.parentElement)) continue;
            let target = node.parentElement;
            const inlineTags = ['span', 'a', 'p', 'em', 'strong', 'b', 'i', 'li', 'td', 'th', 'label', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'small', 'div'];
            if (!target || !inlineTags.includes(target.tagName.toLowerCase()) || (target.innerText && target.innerText.length > 500)) {
                target = null;
            }
            results.push({ text, element: target, textNode: node });
        }
        return results;
    }

    function applyBlur(element, textNode, level, autoblur) {
        if (!autoblur) return;
        if (textNode && textNode.parentElement) {
            const parent = textNode.parentElement;
            if (parent.classList && parent.classList.contains('codar-shield-wrap')) return;
            const wrapper = document.createElement('span');
            wrapper.className = `codar-shield-wrap codar-blur codar-level-${level}`;
            wrapper.setAttribute('data-codar-flagged', level);
            wrapper.title = 'CODAR Shield: Click to reveal';
            try {
                parent.replaceChild(wrapper, textNode);
                wrapper.appendChild(textNode);
                processedTextNodes.add(textNode);
                wrapper.addEventListener('click', function (e) {
                    e.stopPropagation();
                    this.classList.toggle('codar-revealed');
                });
            } catch (e) {
                flagElement(element || parent, level);
            }
        } else if (element) {
            flagElement(element, level);
        }
    }

    function flagElement(el, level) {
        if (!el || processedElements.has(el)) return;
        processedElements.add(el);
        flaggedCount++;

        el.setAttribute('data-codar-flagged', level);
        el.classList.add('codar-blur', `codar-level-${level}`);
        
        // Media Blurring (Twitter/X specific)
        if (CURRENT_PLATFORM.key === 'twitter') {
            const tweet = el.closest('article') || el.closest('[data-testid="tweet"]');
            if (tweet) {
                const media = tweet.querySelectorAll('[data-testid="tweetPhoto"], [data-testid="videoPlayer"], [data-testid="videoComponent"], [data-testid="card.wrapper"]');
                media.forEach(m => {
                    m.classList.add('codar-video-blur'); // Apply strong blur to media
                    m.setAttribute('data-codar-flagged', level);
                });
            }
        }

        el.addEventListener('click', function (e) {
            e.stopPropagation();
            this.classList.toggle('codar-revealed');
            
            // If we reveal the text, also reveal the media in the same tweet
            const tweet = this.closest('article') || this.closest('[data-testid="tweet"]');
            if (tweet) {
                tweet.querySelectorAll('.codar-video-blur').forEach(m => m.classList.toggle('codar-revealed'));
            }
        });
    }

    // ==================== SCAN LOGIC ====================

    function scanPage(config = {}) {
        if (isOrphaned()) return { results: [], stats: { scanned: 0, flagged: 0 } };

        const autoblur = config.autoblur !== false;
        const textElements = getPlatformTextElements();
        const results = [];
        let totalScanned = 0;
        let totalFlagged = 0;

        textElements.forEach(({ text, element, textNode }) => {
            scannedCount++;
            const classification = classifyText(text);
            if (classification) {
                results.push({
                    text: text,
                    level: classification.level,
                    score: classification.score,
                    keyword: classification.keyword,
                    platform: CURRENT_PLATFORM.key
                });
                applyBlur(element, textNode, classification.level, autoblur);
                if (element) processedElements.add(element);
            }
        });

        results.sort((a, b) => b.score - a.score);
        
        // Update background badge
        safeSendMessage({ action: 'updateBadge', flagged: flaggedCount });

        return {
            results,
            stats: { scanned: scannedCount, flagged: flaggedCount },
            platform: { key: CURRENT_PLATFORM.key, name: CURRENT_PLATFORM.name }
        };
    }

    // ==================== MESSAGE LISTENER ====================

    if (chrome.runtime && chrome.runtime.onMessage) {
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            if (isOrphaned()) return;

            if (message.action === 'scan') {
                chrome.storage.local.get(['codar_autoblur'], (data) => {
                    const result = scanPage({ autoblur: data.codar_autoblur });
                    sendResponse(result);
                });
                return true;
            }
            if (message.action === 'getPageInfo') {
                sendResponse({
                    url: window.location.href,
                    title: document.title,
                    platform: CURRENT_PLATFORM.key,
                    platformName: CURRENT_PLATFORM.name
                });
                return true;
            }
            if (message.action === 'getPlatform') {
                sendResponse({
                    key: CURRENT_PLATFORM.key,
                    name: CURRENT_PLATFORM.name,
                    icon: CURRENT_PLATFORM.icon
                });
                return true;
            }
            if (message.action === 'setAutoblur') {
                if (message.value) {
                    document.querySelectorAll('[data-codar-flagged]').forEach(el => {
                        el.classList.add('codar-blur');
                        el.classList.remove('codar-revealed');
                    });
                } else {
                    document.querySelectorAll('.codar-blur').forEach(el => el.classList.remove('codar-blur'));
                }
                sendResponse({ ok: true });
                return true;
            }
            if (message.action === 'setRealtime') {
                message.value ? startRealtimeObserver() : stopRealtimeObserver();
                sendResponse({ ok: true });
                return true;
            }
            if (message.action === 'get_stats') {
                sendResponse({
                    scanned: scannedCount,
                    flagged: flaggedCount,
                    reported: reportedCount,
                    active: true,
                    platform: CURRENT_PLATFORM.name
                });
                return true;
            }
            if (message.action === 'analyzeSelection') {
                const text = message.text || '';
                const result = classifyText(text);
                sendResponse({ result: result || { level: 'safe', score: 0, keyword: 'none' } });
                return true;
            }
        });
    }

    // ==================== REAL-TIME OBSERVER ====================

    let observer = null;
    let observerDebounce = null;

    function startRealtimeObserver() {
        if (observer || isOrphaned()) return;
        observer = new MutationObserver((mutations) => {
            clearTimeout(observerDebounce);
            observerDebounce = setTimeout(() => {
                if (isOrphaned()) return;
                processNewNodes(mutations);
            }, 500);
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    function processNewNodes(mutations) {
        chrome.storage.local.get(['codar_autoblur'], (data) => {
            const autoblur = data.codar_autoblur !== false;
            mutations.forEach(m => {
                m.addedNodes.forEach(node => {
                    if (node.nodeType !== 1) return;
                    if (node.classList && node.classList.contains('codar-shield-wrap')) return;
                    const targets = [];
                    if (CURRENT_PLATFORM.selectors.length > 0) {
                        for (const sel of CURRENT_PLATFORM.selectors) {
                            try {
                                if (node.matches && node.matches(sel)) targets.push(node);
                                if (node.querySelectorAll) node.querySelectorAll(sel).forEach(el => targets.push(el));
                            } catch (e) { }
                        }
                    }
                    if (targets.length === 0) {
                        const text = (node.innerText || node.textContent || '').trim();
                        if (text.length >= 5 && text.length <= 2000) targets.push(node);
                    }
                    targets.forEach(el => {
                        if (processedElements.has(el)) return;
                        if (isExcluded(el)) return;
                        const text = (el.innerText || el.textContent || '').trim();
                        if (text.length < 5) return;
                        const classification = classifyText(text);
                        if (classification) {
                            processedElements.add(el);
                            flagElement(el, classification.level);
                            if (!autoblur) el.classList.remove('codar-blur');
                        }
                    });
                });
            });
        });
    }

    function stopRealtimeObserver() {
        if (observer) {
            observer.disconnect();
            observer = null;
            clearTimeout(observerDebounce);
        }
    }

    // ==================== AUTO-START LOGIC ====================
    // This ensures the extension works IMMEDIATELY without clicking the popup.

    let autoblurEnabled = true;
    let realtimeEnabled = true;

    function startInitialScan() {
        if (isOrphaned()) return;
        
        // Immediate scan
        scanPage({ autoblur: autoblurEnabled });
        
        // Second scan after a short delay (for dynamic SPAs like Twitter)
        setTimeout(() => {
            if (!isOrphaned()) scanPage({ autoblur: autoblurEnabled });
        }, 2000);
        
        // Third scan for slow-loading items
        setTimeout(() => {
            if (!isOrphaned()) scanPage({ autoblur: autoblurEnabled });
        }, 5000);
    }

    // Load settings and START AUTOMATICALLY
    chrome.storage.local.get(['codar_realtime', 'codar_autoblur'], (data) => {
        if (isOrphaned()) return;

        autoblurEnabled = data.codar_autoblur !== false;
        realtimeEnabled = data.codar_realtime !== false;

        console.log(`[CODAR Shield] Auto-start: Blurring=${autoblurEnabled}, Realtime=${realtimeEnabled}`);

        // Start scanning immediately
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            startInitialScan();
        } else {
            window.addEventListener('load', startInitialScan);
        }

        // Start real-time observer automatically
        if (realtimeEnabled) {
            startRealtimeObserver();
        }
    });

    // Handle URL changes (Single Page Apps like Twitter/YouTube)
    let lastUrl = location.href;
    setInterval(() => {
        if (location.href !== lastUrl) {
            lastUrl = location.href;
            console.log('[CODAR Shield] URL change detected, re-scanning...');
            if (!isOrphaned()) startInitialScan();
        }
    }, 1000);

})();
