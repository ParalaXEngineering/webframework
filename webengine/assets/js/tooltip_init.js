/**
 * Tooltip Initialization Script
 * 
 * Scans DOM for keywords in .card-body elements and initializes Bootstrap popovers.
 * Only processes tooltips within allowed HTML elements (configurable via window.tooltipAllowedElements).
 */

(function() {
    'use strict';
    
    if (!window.tooltipData || typeof window.tooltipData !== 'object') {
        console.log('No tooltip data available');
        return;
    }
    
    // Validate tooltipData structure - should be {keyword: {content, type, strategy}, ...}
    const keys = Object.keys(window.tooltipData);
    if (keys.length === 0) {
        console.log('Tooltip data is empty');
        return;
    }
    
    // Check if it's actually tooltip data (not a displayer object)
    const firstKey = keys[0];
    const firstValue = window.tooltipData[firstKey];
    if (!firstValue || typeof firstValue !== 'object' || !firstValue.hasOwnProperty('content')) {
        console.error('Invalid tooltip data structure. Expected {keyword: {content, type, strategy}, ...}, got:', window.tooltipData);
        return;
    }
    
    console.log('Initializing tooltips:', keys.length, 'keywords');
    
    // Get allowed elements from config or use default
    const allowedElements = window.tooltipAllowedElements || ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th', 'label', 'span', 'div', 'select'];
    console.log('Tooltip allowed elements:', allowedElements);
    
    // Sort keywords by length (longest first) to avoid partial matches
    const keywords = keys.sort((a, b) => b.length - a.length);
    
    // Track processed nodes to avoid re-processing
    const processedNodes = new WeakSet();
    
    /**
     * Create regex pattern based on matching strategy
     */
    function createPattern(keyword, strategy) {
        // Escape special regex characters
        const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        
        switch (strategy) {
            case 'word_boundary':
                return new RegExp('\\b' + escaped + '\\b', 'gi');
            case 'regex':
                try {
                    return new RegExp(keyword, 'gi');
                } catch (e) {
                    console.warn('Invalid regex pattern:', keyword, e);
                    return null;
                }
            case 'exact':
            default:
                return new RegExp(escaped, 'gi');
        }
    }
    
    /**
     * Check if element's immediate parent is allowed for tooltips
     */
    function isInAllowedElement(node) {
        // Only check the direct parent element, not ancestors
        const parent = node.parentElement;
        if (!parent) {
            return false;
        }
        
        const tagName = parent.tagName.toLowerCase();
        
        // Special case: ignore structural divs (card-body, containers, etc.)
        if (tagName === 'div') {
            // Only allow divs that don't have structural classes
            const structuralClasses = ['card-body', 'card', 'card-header', 'container', 'row', 'col'];
            const hasStructuralClass = structuralClasses.some(cls => 
                parent.classList && parent.classList.contains(cls)
            );
            return !hasStructuralClass && allowedElements.includes(tagName);
        }
        
        return allowedElements.includes(tagName);
    }
    
    /**
     * Strip HTML tags for plain text content (used for select options)
     */
    function stripHtml(html) {
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        return tmp.textContent || tmp.innerText || '';
    }
    
    /**
     * Process select elements - add native tooltips to options with matching keywords
     */
    function processSelectElement(selectElement) {
        if (processedNodes.has(selectElement)) {
            return;
        }
        
        const options = selectElement.querySelectorAll('option');
        options.forEach(function(option) {
            const originalText = option.textContent.trim();
            if (!originalText) return;
            
            // Find matching tooltips
            for (const keyword of keywords) {
                const tooltip = window.tooltipData[keyword];
                const pattern = createPattern(keyword, tooltip.strategy);
                
                if (!pattern) continue;
                
                pattern.lastIndex = 0;
                if (pattern.test(originalText)) {
                    // Get plain text content from tooltip
                    const tooltipText = stripHtml(tooltip.content);
                    
                    // Add title attribute for browser native tooltip (shown on hover)
                    option.title = tooltipText;
                    
                    break; // Only add first matching tooltip per option
                }
            }
        });
        
        processedNodes.add(selectElement);
    }
    
    /**
     * Wrap keyword matches in span elements
     */
    function wrapKeywords(node) {
        if (processedNodes.has(node)) {
            return;
        }
        
        // Skip certain elements
        if (node.nodeType === Node.ELEMENT_NODE) {
            const tagName = node.tagName.toLowerCase();
            
            // Skip scripts, styles, code blocks, and form inputs
            if (['script', 'style', 'code', 'pre', 'textarea', 'input', 'button'].includes(tagName)) {
                return;
            }
            
            // Special handling for select elements
            if (tagName === 'select' && allowedElements.includes('select')) {
                processSelectElement(node);
                return;
            }
            
            // Skip if already a tooltip span
            if (node.classList && node.classList.contains('has-tooltip')) {
                return;
            }
        }
        
        // Process text nodes only if they're in allowed elements
        if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
            // Check if parent element is allowed
            if (!isInAllowedElement(node)) {
                return;
            }
            
            let text = node.textContent;
            let modified = false;
            const fragments = [];
            let lastIndex = 0;
            
            // Track all matches across all keywords
            const matches = [];
            
            for (const keyword of keywords) {
                const tooltip = window.tooltipData[keyword];
                const pattern = createPattern(keyword, tooltip.strategy);
                
                if (!pattern) continue;
                
                let match;
                pattern.lastIndex = 0;
                
                while ((match = pattern.exec(text)) !== null) {
                    matches.push({
                        keyword: keyword,
                        tooltip: tooltip,
                        start: match.index,
                        end: match.index + match[0].length,
                        text: match[0]
                    });
                }
            }
            
            if (matches.length === 0) {
                return;
            }
            
            // Sort matches by start position
            matches.sort((a, b) => a.start - b.start);
            
            // Remove overlapping matches (keep first one)
            const nonOverlapping = [];
            let lastEnd = -1;
            for (const match of matches) {
                if (match.start >= lastEnd) {
                    nonOverlapping.push(match);
                    lastEnd = match.end;
                }
            }
            
            // Build new content with wrapped keywords
            const parent = node.parentNode;
            const fragment = document.createDocumentFragment();
            
            lastIndex = 0;
            for (const match of nonOverlapping) {
                // Add text before match
                if (match.start > lastIndex) {
                    fragment.appendChild(document.createTextNode(text.substring(lastIndex, match.start)));
                }
                
                // Create tooltip span
                const span = document.createElement('span');
                span.className = 'has-tooltip';
                span.textContent = match.text;
                span.dataset.keyword = match.keyword;
                span.dataset.tooltipContent = match.tooltip.content;
                span.dataset.tooltipType = match.tooltip.type;
                
                // Set Bootstrap popover attributes
                span.setAttribute('data-bs-toggle', 'popover');
                span.setAttribute('data-bs-trigger', 'hover focus');
                span.setAttribute('data-bs-placement', 'auto');
                span.setAttribute('data-bs-html', match.tooltip.type === 'html' ? 'true' : 'false');
                span.setAttribute('data-bs-content', match.tooltip.content);
                span.setAttribute('tabindex', '0');
                
                // Styling
                span.style.borderBottom = '1px dotted #666';
                span.style.cursor = 'help';
                
                fragment.appendChild(span);
                lastIndex = match.end;
            }
            
            // Add remaining text
            if (lastIndex < text.length) {
                fragment.appendChild(document.createTextNode(text.substring(lastIndex)));
            }
            
            // Replace original node
            parent.replaceChild(fragment, node);
            processedNodes.add(parent);
            modified = true;
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            // Recursively process child nodes
            // Create array copy since we'll be modifying the tree
            const children = Array.from(node.childNodes);
            for (const child of children) {
                wrapKeywords(child);
            }
        }
    }
    
    /**
     * Initialize tooltips on page load
     */
    function initializeTooltips() {
        // Find all .card-body elements on the page
        const cardBodies = document.querySelectorAll('.card-body');
        
        if (cardBodies.length === 0) {
            console.warn('No .card-body elements found for tooltip processing');
            return;
        }
        
        console.log(`Processing tooltips in ${cardBodies.length} .card-body element(s)`);
        
        // Process each card-body
        cardBodies.forEach(function(cardBody) {
            wrapKeywords(cardBody);
        });
        
        // Initialize Bootstrap popovers
        const tooltipElements = document.querySelectorAll('.has-tooltip');
        console.log('Initializing', tooltipElements.length, 'tooltip popovers');
        
        tooltipElements.forEach(function(element) {
            // Use Bootstrap 5 Popover
            if (typeof bootstrap !== 'undefined' && bootstrap.Popover) {
                new bootstrap.Popover(element, {
                    trigger: 'hover focus',
                    placement: 'auto',
                    html: element.dataset.tooltipType === 'html',
                    content: element.dataset.tooltipContent,
                    container: 'body'
                });
            }
        });
    }
    
    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeTooltips);
    } else {
        // DOM already loaded
        initializeTooltips();
    }
    
})();
