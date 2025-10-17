#!/bin/bash

# Update all vendor libraries to their latest versions
# This script downloads libraries from CDN for offline use

set -e  # Exit on error

VENDORS_DIR="webengine/assets/vendors"
TEMP_DIR=$(mktemp -d)

echo "============================================"
echo "Updating all vendor libraries..."
echo "============================================"
echo ""

# Function to download and extract files
download_library() {
    local name=$1
    local version=$2
    local package=$3
    local files=("${@:4}")
    
    echo "📦 Downloading $name v$version..."
    local target_dir="${VENDORS_DIR}/${name}"
    mkdir -p "$target_dir"
    
    for file in "${files[@]}"; do
        local url="https://cdn.jsdelivr.net/npm/${package}@${version}/${file}"
        local output="${target_dir}/$(basename ${file})"
        echo "   ↓ $(basename ${file})"
        curl -sL -o "$output" "$url"
    done
    
    echo "   ✓ Done"
    echo ""
}

# Get latest version from npm registry
get_latest_version() {
    local package=$1
    curl -s "https://registry.npmjs.org/$package/latest" | grep -o '"version":"[^"]*"' | cut -d'"' -f4
}

# GridStack
GRIDSTACK_VERSION=$(get_latest_version "gridstack")
download_library "gridstack" "$GRIDSTACK_VERSION" "gridstack" \
    "dist/gridstack-all.min.js" \
    "dist/gridstack.min.css"

# jQuery
JQUERY_VERSION=$(get_latest_version "jquery")
download_library "jquery" "$JQUERY_VERSION" "jquery" \
    "dist/jquery.min.js"

# DataTables
DATATABLES_VERSION=$(get_latest_version "datatables.net-bs5")
download_library "datatables.net" "$DATATABLES_VERSION" "datatables.net-bs5" \
    "css/dataTables.bootstrap5.min.css" \
    "js/dataTables.bootstrap5.min.js"

# FullCalendar
FULLCALENDAR_VERSION=$(get_latest_version "@fullcalendar/core")
download_library "fullcalendar" "$FULLCALENDAR_VERSION" "@fullcalendar/core" \
    "index.global.min.js"

# Highlight.js
HIGHLIGHTJS_VERSION=$(get_latest_version "highlight.js")
download_library "highlightjs" "$HIGHLIGHTJS_VERSION" "highlight.js" \
    "styles/default.min.css" \
    "highlight.min.js"

# Perfect Scrollbar
PERFECT_SCROLLBAR_VERSION=$(get_latest_version "perfect-scrollbar")
download_library "perfect-scrollbar" "$PERFECT_SCROLLBAR_VERSION" "perfect-scrollbar" \
    "dist/perfect-scrollbar.min.js" \
    "css/perfect-scrollbar.css"

# SweetAlert2
SWEETALERT_VERSION=$(get_latest_version "sweetalert2")
download_library "sweetalert" "$SWEETALERT_VERSION" "sweetalert2" \
    "dist/sweetalert2.all.min.js" \
    "dist/sweetalert2.min.css"

# Material Design Icons
MDI_VERSION=$(get_latest_version "@mdi/font")
download_library "mdi" "$MDI_VERSION" "@mdi/font" \
    "css/materialdesignicons.min.css"
# Download fonts
echo "📦 Downloading MDI fonts..."
mkdir -p "${VENDORS_DIR}/mdi/fonts"
for font in materialdesignicons-webfont.woff2 materialdesignicons-webfont.woff materialdesignicons-webfont.ttf; do
    echo "   ↓ $font"
    curl -sL -o "${VENDORS_DIR}/mdi/fonts/$font" "https://cdn.jsdelivr.net/npm/@mdi/font@${MDI_VERSION}/fonts/$font"
done
echo "   ✓ Done"
echo ""

# FilePond
FILEPOND_VERSION=$(get_latest_version "filepond")
download_library "filepond" "$FILEPOND_VERSION" "filepond" \
    "dist/filepond.min.js" \
    "dist/filepond.min.css"

# FilePond Image Preview Plugin
FILEPOND_IMAGE_VERSION=$(get_latest_version "filepond-plugin-image-preview")
download_library "filepond-plugin-image-preview" "$FILEPOND_IMAGE_VERSION" "filepond-plugin-image-preview" \
    "dist/filepond-plugin-image-preview.min.js" \
    "dist/filepond-plugin-image-preview.min.css"

# FilePond File Validate Type Plugin
FILEPOND_VALIDATE_VERSION=$(get_latest_version "filepond-plugin-file-validate-type")
download_library "filepond-plugin-file-validate-type" "$FILEPOND_VALIDATE_VERSION" "filepond-plugin-file-validate-type" \
    "dist/filepond-plugin-file-validate-type.min.js"

# TinyMCE (special case - need to download whole package)
echo "📦 Downloading TinyMCE (this may take a moment)..."
TINYMCE_VERSION=$(get_latest_version "tinymce")
TINYMCE_URL="https://cdn.jsdelivr.net/npm/tinymce@${TINYMCE_VERSION}/tinymce.min.js"
mkdir -p "${VENDORS_DIR}/tinymce"
curl -sL -o "${VENDORS_DIR}/tinymce/tinymce.min.js" "$TINYMCE_URL"
echo "   ✓ Done (Note: TinyMCE may need additional files for full functionality)"
echo ""

# Clean up
rm -rf "$TEMP_DIR"

echo "============================================"
echo "✅ All vendor libraries updated successfully!"
echo "============================================"
echo ""
echo "Summary of installed versions:"
echo "  • GridStack: $GRIDSTACK_VERSION"
echo "  • jQuery: $JQUERY_VERSION"
echo "  • DataTables: $DATATABLES_VERSION"
echo "  • FullCalendar: $FULLCALENDAR_VERSION"
echo "  • Highlight.js: $HIGHLIGHTJS_VERSION"
echo "  • Perfect Scrollbar: $PERFECT_SCROLLBAR_VERSION"
echo "  • SweetAlert2: $SWEETALERT_VERSION"
echo "  • Material Design Icons: $MDI_VERSION"
echo "  • FilePond: $FILEPOND_VERSION"
echo "  • FilePond Image Preview: $FILEPOND_IMAGE_VERSION"
echo "  • FilePond Validate Type: $FILEPOND_VALIDATE_VERSION"
echo "  • TinyMCE: $TINYMCE_VERSION"
echo ""
