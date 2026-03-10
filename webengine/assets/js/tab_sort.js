/**
 * Tab Sort & Management
 * 
 * Handles drag-to-reorder tabs (via SortableJS), delete buttons on tabs,
 * and hidden input synchronization for form submission.
 */
(function () {
    "use strict";

    /**
     * Initialize sortable tabs on all [data-sortable-tabs] elements.
     */
    function initSortableTabs() {
        var tabLists = document.querySelectorAll('[data-sortable-tabs="true"]');
        tabLists.forEach(function (ul) {
            if (ul._sortableInitialized) return;
            ul._sortableInitialized = true;

            var tabContentId = ul.id + '_content';
            var tabContent = document.getElementById(tabContentId);

            Sortable.create(ul, {
                animation: 150,
                handle: '.tab-drag-handle',
                draggable: '.sortable-tab-item',
                ghostClass: 'sortable-tab-ghost',
                chosenClass: 'sortable-tab-chosen',
                filter: '.tab-add-item',  // Don't drag the "+" button
                onEnd: function (evt) {
                    if (evt.oldIndex === evt.newIndex) return;
                    syncPaneOrder(ul, tabContent);
                    updateHiddenInputs(ul);
                }
            });
        });
    }

    /**
     * Reorder tab-pane divs to match the new tab header order.
     */
    function syncPaneOrder(ul, tabContent) {
        if (!tabContent) return;

        var tabs = ul.querySelectorAll('.sortable-tab-item');
        var panes = {};

        // Index current panes by their data-tab-index
        tabContent.querySelectorAll('.tab-pane').forEach(function (pane) {
            panes[pane.getAttribute('data-tab-index')] = pane;
        });

        // Re-append panes in the new tab order
        tabs.forEach(function (tab) {
            var idx = tab.getAttribute('data-tab-index');
            var pane = panes[idx];
            if (pane) {
                tabContent.appendChild(pane);
            }
        });
    }

    /**
     * After reorder: create/update a hidden input with the new order
     * so the form submission includes the reorder information.
     */
    function updateHiddenInputs(ul) {
        var reorderName = ul.getAttribute('data-reorder-name');
        if (!reorderName) return;

        // Build the new order array from current DOM position
        var order = [];
        ul.querySelectorAll('.sortable-tab-item').forEach(function (tab) {
            order.push(tab.getAttribute('data-tab-index'));
        });

        // Find or create the hidden input inside the closest form
        var form = ul.closest('form');
        if (!form) return;

        var inputId = 'reorder_' + ul.id;
        var input = document.getElementById(inputId);
        if (!input) {
            input = document.createElement('input');
            input.type = 'hidden';
            input.id = inputId;
            input.name = reorderName;
            form.appendChild(input);
        }
        input.value = JSON.stringify(order);
    }

    /**
     * Handle delete button clicks on tabs.
     * Creates a hidden input and submits the form.
     */
    function initDeleteButtons() {
        document.addEventListener('click', function (e) {
            var btn = e.target.closest('.btn-close-tab');
            if (!btn) return;

            e.preventDefault();
            e.stopPropagation();

            var deleteName = btn.getAttribute('data-delete-name');
            if (!deleteName) return;

            // Confirmation
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: 'Delete this item?',
                    text: 'This action cannot be undone.',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#d33',
                    confirmButtonText: 'Delete'
                }).then(function (result) {
                    if (result.isConfirmed) {
                        submitDelete(btn, deleteName);
                    }
                });
            } else if (confirm('Delete this item?')) {
                submitDelete(btn, deleteName);
            }
        });
    }

    /**
     * Submit a delete action via hidden input in the form.
     */
    function submitDelete(btn, deleteName) {
        var form = btn.closest('form');
        if (!form) return;

        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = deleteName;
        input.value = '1';
        form.appendChild(input);
        form.submit();
    }

    // Initialize on DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function () {
        initSortableTabs();
        initDeleteButtons();
    });

    // Re-initialize after dynamic content loads (e.g., SocketIO updates)
    if (typeof MutationObserver !== 'undefined') {
        var observer = new MutationObserver(function (mutations) {
            var shouldInit = false;
            mutations.forEach(function (m) {
                if (m.addedNodes.length > 0) {
                    m.addedNodes.forEach(function (node) {
                        if (node.nodeType === 1 && (
                            node.querySelector && node.querySelector('[data-sortable-tabs]')
                        )) {
                            shouldInit = true;
                        }
                    });
                }
            });
            if (shouldInit) {
                initSortableTabs();
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }
})();
