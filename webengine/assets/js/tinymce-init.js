// ============================================================================
// TINYMCE INITIALIZATION
// Configure TinyMCE rich text editor
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Check if TinyMCE is loaded
    if (typeof tinymce === 'undefined') {
        console.warn('TinyMCE not loaded, skipping initialization');
        return;
    }

    tinymce.init({
        selector: 'textarea',
        plugins: 'lists',
        a_plugin_option: true,
        a_configuration_option: 400,
        promotion: false,
        height: 250,
        resize: true,
        menubar: '',
        toolbar: "undo redo | blocks fontsizeinput | bold italic | align numlist | bullist numlist outdent indent",
    });
});
