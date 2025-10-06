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
        const tableOptions = {
            colReorder: true,
            buttons: getCommonButtons(selector.includes('advanced'), tableId),
            dom: 'BPlfrtip',
            pageLength: 25
        };
        const finalOptions = { ...tableOptions, ...customOptions };
        const table = new DataTable(`#${tableId}`, finalOptions);
        if (ajax) {
            setInterval(function () {
                fetch('/status/logs_api')
                    .then(response => response.json())
                    .then(newData => {
                        table.clear();
                        table.rows.add(newData);
                        table.draw(false);
                        if (table.searchPanes) {
                            table.searchPanes.rebuildPane();
                        }
                    });
            }, 3000);
        }
    });
}
