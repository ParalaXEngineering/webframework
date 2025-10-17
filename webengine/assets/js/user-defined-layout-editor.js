/**
 * User-Defined Layout Editor
 * 
 * Provides drag-and-drop interface for creating custom Bootstrap grid layouts
 * using GridStack.js. Exports configuration as JSON for use with USER_DEFINED layouts.
 */

(function() {
    'use strict';

    // Available example fields
    const EXAMPLE_FIELDS = [
        'example1', 'example2', 'example3', 'example4',
        'example5', 'example6', 'example7', 'example8'
    ];

    let grid = null;
    let usedFields = new Set();

    /**
     * Initialize the layout editor
     */
    function initLayoutEditor() {
        const gridContainer = document.querySelector('.grid-stack');
        if (!gridContainer) {
            console.error('GridStack container not found - missing <div class="grid-stack"></div>');
            return;
        }
        
        if (typeof GridStack === 'undefined') {
            console.error('GridStack library not loaded! Check if gridstack-all.min.js is included.');
            // Show error message to user
            gridContainer.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <strong>Error:</strong> GridStack library failed to load. 
                    Please check your internet connection or contact support.
                </div>
            `;
            return;
        }
        
        console.log('Initializing GridStack editor...');

        // Initialize GridStack with Bootstrap 12-column grid
        grid = GridStack.init({
            column: 12,
            cellHeight: 80,
            margin: 4,
            float: false,
            disableOneColumnMode: true,
            animate: true,
            resizable: {
                handles: 'e, se, s, sw, w'
            }
        }, gridContainer);

        // Listen for changes
        grid.on('added removed change', function(event, items) {
            updateUsedFields();
            updateJSON();
        });

        // Load existing layout if present
        loadLayout();
    }

    /**
     * Add a new grid item with field selector
     */
    function addGridItem() {
        const availableFields = EXAMPLE_FIELDS.filter(f => !usedFields.has(f));
        
        if (availableFields.length === 0) {
            alert('All 8 example fields are already in use!');
            return;
        }

        // Default to first available field
        const defaultField = availableFields[0];
        
        // Create grid item element
        const gridItem = document.createElement('div');
        gridItem.className = 'grid-stack-item';
        gridItem.setAttribute('gs-w', '6');
        gridItem.setAttribute('gs-h', '1');
        
        const gridItemContent = document.createElement('div');
        gridItemContent.className = 'grid-stack-item-content';
        gridItemContent.innerHTML = createItemContent(defaultField);
        
        gridItem.appendChild(gridItemContent);
        
        // Add to grid
        grid.addWidget(gridItem);
        
        usedFields.add(defaultField);
        updateJSON();
    }

    /**
     * Create HTML content for a grid item
     */
    function createItemContent(fieldId) {
        const fieldOptions = EXAMPLE_FIELDS
            .map(f => `<option value="${f}" ${f === fieldId ? 'selected' : ''}>${f.toUpperCase()}</option>`)
            .join('');
        
        return `
            <button class="remove-item btn btn-sm btn-danger" onclick="removeGridItem(this)" title="Remove">
                <i class="bi bi-x"></i>
            </button>
            <div class="field-selector-wrapper mb-2">
                <label class="form-label mb-1">Field ID:</label>
                <select class="field-selector form-select form-select-sm" onchange="updateFieldSelection(this)">
                    <option value="">-- Select Field --</option>
                    ${fieldOptions}
                </select>
            </div>
            <div class="field-info text-muted small">
                <i class="bi bi-arrows-move"></i> Drag • 
                <i class="bi bi-arrows-angle-expand"></i> Resize
            </div>
            <span class="span-indicator badge bg-primary">Span: 6</span>
        `;
    }

    /**
     * Update field selection for an item
     */
    window.updateFieldSelection = function(selectElement) {
        const gridItem = selectElement.closest('.grid-stack-item');
        const oldValue = gridItem.getAttribute('data-field-id');
        const newValue = selectElement.value;
        
        if (!newValue) {
            selectElement.value = oldValue || '';
            alert('Please select a field');
            return;
        }
        
        // Check if new field is already used elsewhere
        if (newValue !== oldValue && usedFields.has(newValue)) {
            selectElement.value = oldValue || '';
            alert(`Field "${newValue}" is already in use!`);
            return;
        }
        
        // Update tracking
        if (oldValue) {
            usedFields.delete(oldValue);
        }
        usedFields.add(newValue);
        gridItem.setAttribute('data-field-id', newValue);
        
        updateJSON();
    };

    /**
     * Remove a grid item
     */
    window.removeGridItem = function(button) {
        const gridItem = button.closest('.grid-stack-item');
        const fieldId = gridItem.querySelector('.field-selector').value;
        
        if (fieldId) {
            usedFields.delete(fieldId);
        }
        
        grid.removeWidget(gridItem);
        updateJSON();
    };

    /**
     * Update which fields are currently in use
     */
    function updateUsedFields() {
        usedFields.clear();
        document.querySelectorAll('.grid-stack-item').forEach(item => {
            const select = item.querySelector('.field-selector');
            if (select && select.value) {
                usedFields.add(select.value);
                item.setAttribute('data-field-id', select.value);
            }
        });
        
        // Update span indicators
        document.querySelectorAll('.grid-stack-item').forEach(item => {
            const node = item.gridstackNode;
            const spanIndicator = item.querySelector('.span-indicator');
            if (spanIndicator && node) {
                spanIndicator.textContent = `Span: ${node.w}`;
            }
        });
    }

    /**
     * Export current layout to JSON
     */
    function exportJSON() {
        const items = [];
        
        grid.engine.nodes.forEach(node => {
            const element = node.el;
            const fieldId = element.querySelector('.field-selector')?.value;
            
            if (fieldId) {
                items.push({
                    field_id: fieldId,
                    x: node.x,
                    y: node.y,
                    w: node.w,
                    h: node.h
                });
            }
        });
        
        // Sort by y position, then x position
        items.sort((a, b) => {
            if (a.y !== b.y) return a.y - b.y;
            return a.x - b.x;
        });
        
        return {
            version: '1.0',
            columns: 12,
            items: items
        };
    }

    /**
     * Update JSON preview display
     */
    function updateJSON() {
        const jsonData = exportJSON();
        const jsonPreview = document.getElementById('json-preview');
        
        if (jsonPreview) {
            jsonPreview.textContent = JSON.stringify(jsonData, null, 2);
        }
        
        // Store in hidden input for form submission
        const jsonInput = document.getElementById('layout-json');
        if (jsonInput) {
            jsonInput.value = JSON.stringify(jsonData);
        }
    }

    /**
     * Load layout from existing JSON
     */
    function loadLayout() {
        const jsonInput = document.getElementById('layout-json');
        if (!jsonInput || !jsonInput.value) return;
        
        try {
            const data = JSON.parse(jsonInput.value);
            
            if (data.items && Array.isArray(data.items)) {
                data.items.forEach(item => {
                    // Create grid item element
                    const gridItem = document.createElement('div');
                    gridItem.className = 'grid-stack-item';
                    gridItem.setAttribute('gs-x', item.x);
                    gridItem.setAttribute('gs-y', item.y);
                    gridItem.setAttribute('gs-w', item.w);
                    gridItem.setAttribute('gs-h', item.h);
                    
                    const gridItemContent = document.createElement('div');
                    gridItemContent.className = 'grid-stack-item-content';
                    gridItemContent.innerHTML = createItemContent(item.field_id);
                    
                    gridItem.appendChild(gridItemContent);
                    
                    // Add to grid
                    grid.addWidget(gridItem);
                    usedFields.add(item.field_id);
                });
                
                updateJSON();
            }
        } catch (e) {
            console.error('Failed to load layout:', e);
        }
    }

    /**
     * Clear all grid items
     */
    window.clearLayout = function() {
        if (confirm('Are you sure you want to clear the entire layout?')) {
            grid.removeAll();
            usedFields.clear();
            updateJSON();
        }
    };

    /**
     * Copy JSON to clipboard
     */
    window.copyJSON = function() {
        const jsonData = exportJSON();
        const jsonString = JSON.stringify(jsonData, null, 2);
        
        navigator.clipboard.writeText(jsonString).then(() => {
            const btn = event.target;
            const originalText = btn.textContent;
            btn.textContent = 'Copied!';
            btn.classList.remove('btn-outline-secondary');
            btn.classList.add('btn-success');
            
            setTimeout(() => {
                btn.textContent = originalText;
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-secondary');
            }, 2000);
        }).catch(err => {
            alert('Failed to copy to clipboard');
            console.error('Copy failed:', err);
        });
    };

    /**
     * Add new item button handler
     */
    window.addNewItem = function() {
        addGridItem();
    };

    // Initialize when DOM is ready
    console.log('User-defined layout editor script loaded');
    console.log('GridStack available:', typeof GridStack !== 'undefined');
    console.log('Document state:', document.readyState);
    
    if (document.readyState === 'loading') {
        console.log('Waiting for DOMContentLoaded...');
        document.addEventListener('DOMContentLoaded', initLayoutEditor);
    } else {
        console.log('DOM already loaded, initializing immediately');
        initLayoutEditor();
    }

})();
