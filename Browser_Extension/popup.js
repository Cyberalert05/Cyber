// CODAR Shield v2.0 — Popup Script
// Platform-aware popup with live detection, scan results, and reporting.

(function () {
    'use strict';

    const btnScan = document.getElementById('btn-scan');
    const btnReportAll = document.getElementById('btn-report-all');
    const resultsList = document.getElementById('results-list');
    const emptyState = document.getElementById('empty-state');
    const statScanned = document.getElementById('stat-scanned');
    const statFlagged = document.getElementById('stat-flagged');
    const statReported = document.getElementById('stat-reported');
    const statusDot = document.getElementById('status-dot');
    const configApi = document.getElementById('config-api');
    const configAutoblur = document.getElementById('config-autoblur');
    const configRealtime = document.getElementById('config-realtime');
    const platformIcon = document.getElementById('platform-icon');
    const platformName = document.getElementById('platform-name');
    const platformUrl = document.getElementById('platform-url');
    const platformStatus = document.getElementById('platform-status');
    const platformsGrid = document.getElementById('platforms-grid');

    let scanResults = [];
    let detectedPlatform = 'generic';

    // ==================== PLATFORM ICONS ====================
    const PLATFORM_ICONS = {
        twitter: { icon: '𝕏', class: 'twitter', label: 'Twitter / X' },
        youtube: { icon: '▶', class: 'youtube', label: 'YouTube' },
        instagram: { icon: '📷', class: 'instagram', label: 'Instagram' },
        whatsapp: { icon: '💬', class: 'whatsapp', label: 'WhatsApp Web' },
        facebook: { icon: 'f', class: 'facebook', label: 'Facebook' },
        generic: { icon: '🌐', class: 'generic', label: 'Website' }
    };

    // ==================== DETECT PLATFORM ON OPEN ====================
    // Small delay to ensure content script is ready
    setTimeout(() => {
        try {
            sendToActiveTab({ action: 'getPlatform' }, (response) => {
                if (response && response.key) {
                    detectedPlatform = response.key;
                    const info = PLATFORM_ICONS[response.key] || PLATFORM_ICONS.generic;
                    platformIcon.textContent = info.icon;
                    platformIcon.className = 'platform-icon ' + info.class;
                    platformName.textContent = info.label;

                    if (response.key !== 'generic') {
                        platformStatus.textContent = 'OPTIMIZED';
                        platformStatus.className = 'platform-supported yes';
                    } else {
                        platformStatus.textContent = 'GENERIC';
                        platformStatus.className = 'platform-supported partial';
                    }

                    // Highlight active platform chip
                    document.querySelectorAll('.platform-chip').forEach(chip => {
                        if (chip.dataset.platform === response.key) {
                            chip.classList.add('active');
                        }
                    });
                }
            });

            // Get current tab URL for display
            sendToActiveTab({ action: 'getPageInfo' }, (response) => {
                if (response && response.url) {
                    try {
                        const url = new URL(response.url);
                        platformUrl.textContent = url.hostname + url.pathname.substring(0, 40);
                    } catch (e) {
                        platformUrl.textContent = response.url.substring(0, 50);
                    }
                }
            });
        } catch (e) {
            console.error("Popup initialization error:", e);
        }
    }, 200);

    // ==================== LOAD CONFIG ====================
    chrome.storage.local.get(['codar_api', 'codar_autoblur', 'codar_realtime', 'codar_stats'], (data) => {
        if (data.codar_api) configApi.value = data.codar_api;
        if (data.codar_autoblur !== undefined) configAutoblur.checked = data.codar_autoblur;
        if (data.codar_realtime !== undefined) configRealtime.checked = data.codar_realtime;
        if (data.codar_stats) {
            statScanned.textContent = data.codar_stats.scanned || 0;
            statFlagged.textContent = data.codar_stats.flagged || 0;
            statReported.textContent = data.codar_stats.reported || 0;
        }
    });

    // ==================== SAVE CONFIG ====================
    configApi.addEventListener('change', () => {
        chrome.storage.local.set({ codar_api: configApi.value });
    });

    configAutoblur.addEventListener('change', () => {
        chrome.storage.local.set({ codar_autoblur: configAutoblur.checked });
        sendToActiveTab({ action: 'setAutoblur', value: configAutoblur.checked });
    });

    configRealtime.addEventListener('change', () => {
        chrome.storage.local.set({ codar_realtime: configRealtime.checked });
        sendToActiveTab({ action: 'setRealtime', value: configRealtime.checked });
    });

    // ==================== SCAN ====================
    btnScan.addEventListener('click', () => {
        btnScan.disabled = true;
        btnScan.innerHTML = '<span class="spinner"></span> Scanning...';

        sendToActiveTab({ action: 'scan' }, (response) => {
            btnScan.disabled = false;
            btnScan.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg> Scan Page';

            if (response && response.results) {
                scanResults = response.results;
                renderResults(scanResults);
                updateStats(response.stats);

                // Update platform info from scan
                if (response.platform) {
                    const info = PLATFORM_ICONS[response.platform.key] || PLATFORM_ICONS.generic;
                    platformIcon.textContent = info.icon;
                    platformIcon.className = 'platform-icon ' + info.class;
                    platformName.textContent = info.label;
                }
            } else {
                resultsList.innerHTML = '<div class="empty-state"><div class="icon">⚠️</div><p>Could not scan this page.<br>Try refreshing and scanning again.</p></div>';
            }
        });
    });

    // ==================== REPORT ====================
    btnReportAll.addEventListener('click', () => {
        const reportableResults = scanResults.filter(r => r.level === 'toxic' || r.level === 'warning');
        if (reportableResults.length === 0) {
            showNotification('No flagged content found to report. Scan the page first.', 'warning');
            return;
        }

        btnReportAll.disabled = true;
        btnReportAll.innerHTML = '<span class="spinner"></span> Reporting...';

        const apiUrl = configApi.value || 'http://localhost:3003';

        sendToActiveTab({ action: 'getPageInfo' }, (pageInfo) => {
            const payload = {
                platform: detectedPlatform,
                platform_name: (PLATFORM_ICONS[detectedPlatform] || PLATFORM_ICONS.generic).label,
                page_url: pageInfo ? pageInfo.url : 'unknown',
                page_title: pageInfo ? pageInfo.title : 'unknown',
                flagged_items: reportableResults.map(r => ({
                    text: r.text,
                    score: r.score,
                    level: r.level,
                    keyword: r.keyword
                })),
                total_flagged: reportableResults.length,
                scan_time: new Date().toISOString()
            };

            fetch(apiUrl + '/api/extension-report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => {
                if (res.ok) {
                    const reported = parseInt(statReported.textContent) + reportableResults.length;
                    statReported.textContent = reported;
                    chrome.storage.local.get(['codar_stats'], (data) => {
                        const stats = data.codar_stats || {};
                        stats.reported = reported;
                        chrome.storage.local.set({ codar_stats: stats });
                    });
                    showNotification(`✅ ${reportableResults.length} items reported to CODAR Dashboard!`, 'success');
                } else {
                    throw new Error('Server error');
                }
            })
            .catch(err => {
                console.error('Report error:', err);
                showNotification('❌ Failed to report. Is the Reporting Platform running?', 'error');
            })
            .finally(() => {
                btnReportAll.disabled = false;
                btnReportAll.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" y1="22" x2="4" y2="15"></line></svg> Report All';
            });
        });
    });

    // ==================== RENDER ====================
    function renderResults(results) {
        if (results.length === 0) {
            resultsList.innerHTML = '<div class="empty-state"><div class="icon">✅</div><p>No toxic content detected.<br>This page looks clean!</p></div>';
            return;
        }

        resultsList.innerHTML = '';
        results.forEach((r) => {
            const item = document.createElement('div');
            item.className = 'result-item ' + r.level;
            const scorePercent = (r.score * 100).toFixed(0);
            item.innerHTML = `
                <span class="badge ${r.level}">${r.level} ${scorePercent}%</span>
                <span class="text">${escapeHtml(r.text.substring(0, 120))}${r.text.length > 120 ? '…' : ''}</span>
            `;
            resultsList.appendChild(item);
        });
    }

    function updateStats(stats) {
        if (!stats) return;
        statScanned.textContent = stats.scanned || 0;
        statFlagged.textContent = stats.flagged || 0;
        chrome.storage.local.set({ codar_stats: { ...stats, reported: parseInt(statReported.textContent) || 0 } });
    }

    function showNotification(message, type) {
        // Remove any existing toast
        const existing = document.querySelector('.codar-toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = 'codar-toast';
        const colors = {
            success: 'linear-gradient(135deg, #38ef7d, #11998e)',
            error: 'linear-gradient(135deg, #ff416c, #ff4b2b)',
            warning: 'linear-gradient(135deg, #ffc107, #ffb300)'
        };
        toast.style.cssText = `
            position: fixed; bottom: 12px; left: 12px; right: 12px;
            padding: 12px 16px; border-radius: 10px;
            background: ${colors[type] || colors.success};
            color: ${type === 'warning' ? '#1a1a1a' : '#fff'};
            font-size: 12px; font-weight: 600; text-align: center;
            z-index: 9999; animation: toastIn 0.3s ease;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        `;
        toast.textContent = message;
        document.body.appendChild(toast);

        // Add animation keyframes if not already present
        if (!document.getElementById('toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                @keyframes toastIn { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
                @keyframes toastOut { from { opacity: 1; } to { transform: translateY(20px); opacity: 0; } }
            `;
            document.head.appendChild(style);
        }

        setTimeout(() => {
            toast.style.animation = 'toastOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ==================== HELPERS ====================
    function sendToActiveTab(message, callback) {
        try {
            if (!chrome.runtime || !chrome.runtime.id) {
                console.warn("CODAR: Extension context invalidated.");
                if (callback) callback(null);
                return;
            }

            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                if (chrome.runtime.lastError) {
                    if (callback) callback(null);
                    return;
                }

                if (!tabs || !tabs[0]) {
                    if (callback) callback(null);
                    return;
                }
                const tab = tabs[0];
                const url = tab.url || '';
                
                // Content scripts cannot be injected into restricted pages
                if (url.startsWith('chrome://') || url.startsWith('chrome-extension://') ||
                    url.startsWith('about:') || url.startsWith('edge://') || url === '' ||
                    url.startsWith('https://chrome.google.com/webstore')) {
                    if (callback) callback(null);
                    return;
                }

                // Try to send message
                chrome.tabs.sendMessage(tab.id, message, (response) => {
                    const err = chrome.runtime.lastError;
                    if (err) {
                        if (err.message.includes("Could not establish connection")) {
                            console.log("CODAR: Content script not ready on this tab.");
                        } else if (err.message.includes("context invalidated")) {
                            console.warn("CODAR: Context invalidated. Please refresh the page.");
                            showNotification("⚠️ Extension updated. Please refresh the page.", "warning");
                        }
                        if (callback) callback(null);
                    } else {
                        if (callback) callback(response);
                    }
                });
            });
        } catch (e) {
            console.error("CODAR: sendToActiveTab exception:", e);
            if (callback) callback(null);
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();
