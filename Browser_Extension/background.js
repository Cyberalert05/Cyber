// CODAR Shield v2.0 — Background Service Worker
// Manages badge counts, context menus, and persistent state.

const PLATFORMS = ['twitter', 'youtube', 'instagram', 'whatsapp', 'facebook'];

// ==================== BADGE MANAGEMENT ====================

chrome.runtime.onInstalled.addListener(() => {
    console.log('[CODAR Shield] Extension installed / updated — v2.0');

    // Set default config
    chrome.storage.local.get(['codar_api', 'codar_autoblur', 'codar_realtime', 'codar_stats'], (data) => {
        const defaults = {};
        if (!data.codar_api) defaults.codar_api = 'http://localhost:3003';
        if (data.codar_autoblur === undefined) defaults.codar_autoblur = true;
        if (data.codar_realtime === undefined) defaults.codar_realtime = true;
        if (!data.codar_stats) defaults.codar_stats = { scanned: 0, flagged: 0, reported: 0 };
        if (Object.keys(defaults).length > 0) {
            chrome.storage.local.set(defaults);
        }
    });

    // Set initial badge
    chrome.action.setBadgeBackgroundColor({ color: '#667eea' });
    chrome.action.setBadgeText({ text: '' });

    // Create context menu
    chrome.contextMenus.create({
        id: 'codar-scan-selection',
        title: '🛡️ CODAR: Analyze selected text',
        contexts: ['selection']
    });
});

// ==================== CONTEXT MENU HANDLER ====================

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === 'codar-scan-selection' && info.selectionText) {
        // Send the selected text to the content script for analysis
        chrome.tabs.sendMessage(tab.id, {
            action: 'analyzeSelection',
            text: info.selectionText
        }, (response) => {
            if (chrome.runtime.lastError) {
                console.log('[CODAR Shield] Could not analyze selection:', chrome.runtime.lastError.message);
                return;
            }
            if (response && response.result) {
                const level = response.result.level;
                // Show notification
                chrome.notifications.create({
                    type: 'basic',
                    iconUrl: 'icons/icon128.png',
                    title: `CODAR Shield — ${level === 'toxic' ? '🚨 Toxic' : level === 'warning' ? '⚠️ Warning' : '✅ Safe'}`,
                    message: level === 'toxic'
                        ? `Toxic content detected (${(response.result.score * 100).toFixed(0)}% confidence). Keyword: "${response.result.keyword}"`
                        : level === 'warning'
                            ? `Suspicious content (${(response.result.score * 100).toFixed(0)}% confidence). Keyword: "${response.result.keyword}"`
                            : 'No toxic content detected in the selected text.',
                    priority: level === 'toxic' ? 2 : 1
                });
            }
        });
    }
});

// ==================== TAB CHANGE — UPDATE BADGE ====================

chrome.tabs.onActivated.addListener(async (activeInfo) => {
    try {
        const tab = await chrome.tabs.get(activeInfo.tabId);
        updateBadgeForUrl(tab.url);
    } catch (e) {
        // Tab may have been closed
    }
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.active) {
        updateBadgeForUrl(tab.url);
    }
});

function updateBadgeForUrl(url) {
    if (!url) return;

    let platform = null;
    for (const p of PLATFORMS) {
        if (p === 'twitter' && /(twitter\.com|x\.com)/i.test(url)) { platform = 'twitter'; break; }
        if (p === 'youtube' && /youtube\.com/i.test(url)) { platform = 'youtube'; break; }
        if (p === 'instagram' && /instagram\.com/i.test(url)) { platform = 'instagram'; break; }
        if (p === 'whatsapp' && /web\.whatsapp\.com/i.test(url)) { platform = 'whatsapp'; break; }
        if (p === 'facebook' && /(facebook\.com|fb\.com)/i.test(url)) { platform = 'facebook'; break; }
    }

    if (platform) {
        chrome.action.setBadgeText({ text: '●' });
        chrome.action.setBadgeBackgroundColor({ color: '#38ef7d' });
    } else {
        chrome.action.setBadgeText({ text: '' });
    }
}

// ==================== MESSAGE RELAY ====================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'updateBadge') {
        const flagged = message.flagged || 0;
        if (flagged > 0) {
            chrome.action.setBadgeText({ text: String(flagged) });
            chrome.action.setBadgeBackgroundColor({ color: '#ff416c' });
        } else {
            chrome.action.setBadgeText({ text: '✓' });
            chrome.action.setBadgeBackgroundColor({ color: '#38ef7d' });
        }
        sendResponse({ ok: true });
        return true;
    }
});
