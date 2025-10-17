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

    // TinyMCE Configuration
    // For TinyMCE 6+, you need a free API key from: https://www.tiny.cloud/auth/signup/
    // Set your API key as a global variable before loading TinyMCE, or add it here:
    const config = {
        selector: 'textarea',
        
        // API key for self-hosted GPL version (free)
        license_key: 'gpl',  // Use 'gpl' for self-hosted GPL version
        
        // Or get a free cloud API key from: https://www.tiny.cloud/auth/signup/
        // and set: license_key: 'your-api-key-here'
        
        // Plugins and features
        plugins: 'lists link image table code help wordcount',
        toolbar: 'undo redo | blocks fontsize | bold italic underline | alignleft aligncenter alignright | bullist numlist | link image | code',
        
        // Editor settings
        height: 250,
        resize: true,
        menubar: false,
        promotion: false,  // Disable upgrade prompts
        branding: false,   // Remove "Powered by TinyMCE" (allowed in free tier)
        
        // Content styling
        content_style: 'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 14px; }',
    };
    
    // Use global API key if set
    if (window.TINYMCE_API_KEY) {
        config.license_key = window.TINYMCE_API_KEY;
    }
    
    // Initialize TinyMCE
    tinymce.init(config);
});
