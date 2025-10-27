// ============================================================================
// DATATABLES INITIALIZATION
// Configure DataTables library with common buttons and settings
// ============================================================================

// Function to create common buttons
function getCommonButtons(checkAll, elementId) {
    return [
        {
            text: checkAll ? 'Check All' : 'Check All',
            action: function (e, dt, node, config) {
                const isChecked = $(node).text() === 'Check All';
                const checkboxes = dt.table().node().querySelectorAll(`input[type="checkbox"]`);
                checkboxes.forEach(checkbox => checkbox.checked = isChecked);
                $(node).text(isChecked ? 'Uncheck All' : 'Check All');
            }
        },
        {
            text: 'Export',
            action: function () {},
            split: ['pdf', 'excel', 'print', 'copy']
        },
        {
            text: 'View',
            action: function () {},
            split: [
                { text: 'Show 10 items', action: (e, dt) => dt.page.len(10).draw() },
                { text: 'Show 25 items', action: (e, dt) => dt.page.len(25).draw() },
                { text: 'Show 50 items', action: (e, dt) => dt.page.len(50).draw() },
                { text: 'Show 100 items', action: (e, dt) => dt.page.len(100).draw() }
            ]
        }
    ];
}

function initializeDataTable(selector, customOptions, ajax) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(element => {
        const tableId = element.id;
        
        // Base options
        const tableOptions = {
            colReorder: true,
            buttons: getCommonButtons(selector.includes('advanced'), tableId),
            pageLength: 25
        };
        
        // If customOptions uses the new 'layout' API (DT2), don't use old 'dom' string
        // The 'dom' and 'layout' configurations conflict with each other
        if (!customOptions.layout) {
            // Use old dom string for backward compatibility (DT1.x style)
            tableOptions.dom = 'BPlfrtip';
        }
        
        const finalOptions = { ...tableOptions, ...customOptions };
        const table = new DataTable(`#${tableId}`, finalOptions);
        // Note: Auto-refresh removed - use customOptions.ajax with proper endpoint if needed
    });
}
