// ============================================================================
// FILEPOND INITIALIZATION
// Configure FilePond file upload library
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Check if FilePond is loaded
    if (typeof FilePond === 'undefined') {
        console.warn('FilePond not loaded, skipping initialization');
        return;
    }

    // Register plugins
    if (typeof FilePondPluginImagePreview !== 'undefined' && typeof FilePondPluginFileValidateType !== 'undefined') {
        FilePond.registerPlugin(FilePondPluginImagePreview, FilePondPluginFileValidateType);
    }

    // Filepond: Image Preview
    const filePondImage = document.querySelectorAll(".image-preview-filepond");
    filePondImage.forEach(element => {
        FilePond.create(element, {
            labelIdle: `Drag & Drop image <span class="filepond--label-action">Browse</span>`,
            credits: null,
            allowImagePreview: true,
            allowImageFilter: false,
            allowImageExifOrientation: false,
            allowImageCrop: false,
            acceptedFileTypes: ["image/png", "image/jpg", "image/jpeg"],
            fileValidateTypeDetectType: (source, type) => new Promise((resolve, reject) => {
                resolve(type);
            }),
            storeAsFile: true,
        });
    });

    // Filepond: Base
    const filePondBase = document.querySelectorAll(".basic-filepond");
    filePondBase.forEach(element => {
        FilePond.create(element, {
            credits: null,
            storeAsFile: true,
        });
    });

    // Filepond: Folder
    const filePondFolder = document.querySelectorAll(".folder-filepond");
    filePondFolder.forEach(element => {
        FilePond.create(element, {
            credits: null,
            storeAsFile: true,
            labelIdle: `Drag & Drop a zip file <span class="filepond--label-action">Browse</span>`,
            acceptedFileTypes: ['application/x-zip-compressed']
        });
    });
});
