/**
 * Thread Monitor - Real-time thread status updates via Socket.IO
 * 
 * Listens for thread_update events and dynamically updates the thread cards
 * without requiring page refresh.
 */

(function() {
    'use strict';
    
    // Only run on thread monitor page
    if (!window.location.pathname.includes('/threads')) {
        return;
    }
    
    console.log('[Thread Monitor] Initializing real-time updates');
    
    // Wait for Socket.IO to be available (initialized by site.js)
    function initThreadMonitor() {
        if (typeof window.socket === 'undefined' || !window.socket) {
            console.log('[Thread Monitor] Waiting for socket connection...');
            setTimeout(initThreadMonitor, 100);
            return;
        }
        
        console.log('[Thread Monitor] Socket connection found, setting up listeners');
        
        var socket = window.socket;
        
        // Listen for thread updates
        socket.on('thread_update', function(data) {
            console.log('[Thread Monitor] Received update:', data);
            updateThreadDisplay(data);
        });
        
        console.log('[Thread Monitor] Real-time updates initialized');
    }
    
    // Start initialization
    initThreadMonitor();
    
    /**
     * Update the thread display with new data
     */
    function updateThreadDisplay(data) {
        // Update statistics
        updateStats(data.stats);
        
        // Update running threads
        updateRunningThreads(data.running);
        
        // Update completed threads history
        updateCompletedThreads(data.completed);
    }
    
    /**
     * Update statistics section
     */
    function updateStats(stats) {
        // Find stat elements and update them
        const statDivs = document.querySelectorAll('.text-center h3');
        if (statDivs.length >= 4) {
            statDivs[0].textContent = stats.total || 0;
            statDivs[1].textContent = stats.running || 0;
            // statDivs[2] is "With Process" - keep existing
            statDivs[3].textContent = stats.with_error || 0;
        }
    }
    
    /**
     * Update running threads section
     */
    function updateRunningThreads(threads) {
        if (!threads || threads.length === 0) {
            // Show "no threads" message if section exists
            const runningSection = document.querySelector('h4 i.mdi-play-circle');
            if (runningSection) {
                const container = runningSection.closest('.row');
                if (container) {
                    // Find running thread cards and remove them
                    const cards = container.querySelectorAll('.card');
                    cards.forEach(card => {
                        if (!card.classList.contains('border-secondary')) { // Not history
                            card.closest('.row')?.remove();
                        }
                    });
                }
            }
            return;
        }
        
        // Update each running thread
        threads.forEach(thread => {
            updateThreadCard(thread, true);
        });
    }
    
    /**
     * Update completed threads history section
     */
    function updateCompletedThreads(threads) {
        if (!threads || threads.length === 0) {
            return;
        }
        
        // Update each completed thread
        threads.forEach(thread => {
            updateThreadCard(thread, false);
        });
    }
    
    /**
     * Update or create a thread card
     */
    function updateThreadCard(thread, isRunning) {
        const cardId = `thread_card_${sanitizeId(thread.name)}`;
        let card = document.getElementById(cardId);
        
        if (!card) {
            // Card doesn't exist - log once and skip silently thereafter
            if (!updateThreadCard.missingCards) {
                updateThreadCard.missingCards = {};
            }
            if (!updateThreadCard.missingCards[cardId]) {
                console.log(`[Thread Monitor] Card ${cardId} not found, skipping updates`);
                updateThreadCard.missingCards[cardId] = true;
            }
            return;
        }
        
        // Update console output (in first tab pane)
        const tab1 = card.querySelector('#tab1');
        if (tab1 && thread.console) {
            // Find the console div with dark background
            const consoleEl = tab1.querySelector('div[style*="background:#1e1e1e"]');
            if (consoleEl) {
                // Update console content (last 50 lines)
                let consoleHtml = '';
                const lines = thread.console.slice(-50);
                lines.forEach(line => {
                    consoleHtml += escapeHtml(line) + '<br>';
                });
                consoleEl.innerHTML = consoleHtml;
                // Auto-scroll to bottom
                consoleEl.scrollTop = consoleEl.scrollHeight;
            } else if (thread.console.length > 0) {
                // Console div doesn't exist but we have output - create it
                const consoleHtml = `<div style='background:#1e1e1e; color:#d4d4d4; padding:10px; border-radius:5px; max-height:400px; overflow-y:auto; font-family:monospace;'>
                    ${thread.console.slice(-50).map(line => escapeHtml(line)).join('<br>')}
                </div>`;
                tab1.innerHTML = consoleHtml;
            }
        }
        
        // Update logs (in second tab pane)
        const tab2 = card.querySelector('#tab2');
        if (tab2 && thread.logs && thread.logs.length > 0) {
            let logsHtml = "<div style='max-height:400px; overflow-y:auto;'>";
            logsHtml += "<table class='table table-sm table-striped'>";
            logsHtml += "<thead><tr><th>Level</th><th>Message</th><th>Data</th></tr></thead><tbody>";
            
            // Show last 30 logs
            const recentLogs = thread.logs.slice(-30);
            recentLogs.forEach(entry => {
                const levelBadge = {
                    'debug': 'secondary',
                    'info': 'info',
                    'warning': 'warning',
                    'error': 'danger',
                    'DEBUG': 'secondary',
                    'INFO': 'info',
                    'WARNING': 'warning',
                    'ERROR': 'danger'
                }[entry.level] || 'secondary';
                
                logsHtml += `<tr>
                    <td><span class="badge bg-${levelBadge}">${entry.level}</span></td>
                    <td>${escapeHtml(entry.message || '')}</td>
                    <td><small>${escapeHtml(JSON.stringify(entry.data || {}))}</small></td>
                </tr>`;
            });
            
            logsHtml += "</tbody></table></div>";
            
            // Replace entire tab content
            tab2.innerHTML = logsHtml;
        }
        
        // Update stats in Info tab (4th tab pane) if exists
        const tab4 = card.querySelector('#tab4');
        if (tab4) {
            const dl = tab4.querySelector('dl.row');
            if (dl) {
                // Update Running status
                const dtElements = dl.querySelectorAll('dt');
                dtElements.forEach((dt, index) => {
                    if (dt.textContent.trim() === 'Running:') {
                        const dd = dt.nextElementSibling;
                        if (dd && thread.status) {
                            dd.textContent = thread.status === 'running' ? 'Yes' : 'No';
                        }
                    } else if (dt.textContent.trim() === 'Progress:') {
                        const dd = dt.nextElementSibling;
                        if (dd && thread.progress !== undefined) {
                            dd.textContent = `${thread.progress}%`;
                        }
                    }
                });
            }
        }
    }
    
    /**
     * Sanitize string for use as HTML ID (must match Python sanitization)
     * Python: thread_name.replace(' ', '_').replace(':', '_')
     */
    function sanitizeId(str) {
        return str.replace(/ /g, '_').replace(/:/g, '_');
    }
    
    /**
     * Escape HTML special characters
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    console.log('[Thread Monitor] Real-time updates initialized');
})();
