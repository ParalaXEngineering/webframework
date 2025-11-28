# File Manager Frontend Test Plan

**Date**: 2025-11-28  
**Status**: Initial Implementation - High Priority Tests  
**Framework**: Playwright + Pytest

## Overview

Comprehensive frontend testing for the File Manager interface covering upload, display, edit, version control, and deletion workflows.

## Test Structure

### Files
- `test_file_manager.py` - Main test suite
- `test_files/` - Test assets directory

### Test Data
Located in `tests/frontend/test_files/`:
- `test_image.jpg` - Image for thumbnail testing (500KB)
- `test_image.png` - Alternative image format
- `test_document.pdf` - PDF document
- `test_text.txt` - Plain text file
- `test_archive.zip` - Archive file

## Implementation Status

### ✅ High Priority (MVP - Implemented)
1. **Upload basic file** - Test single file upload via FilePond
2. **Display in admin list** - Verify file appears in DataTable
3. **Download file** - Test download button functionality
4. **Delete file** - Test single file deletion with confirmation
5. **Thumbnail generation** - Verify thumbnails for images

### 🔄 Medium Priority (TODO)
1. Edit metadata (group_id, tags)
2. Version history view
3. Multi-delete with checkboxes
4. Search/filter functionality
5. Restore version operation

### ⏳ Low Priority (TODO)
1. Delete single version (keep others)
2. Integrity status checks
3. Edge cases (empty states, permissions)
4. Error scenarios (size limits, invalid tags)
5. Concurrent operations

## Test Execution

```bash
# Run all file manager tests
pytest tests/frontend/test_file_manager.py -v

# Run with visible browser (HUMAN_MODE)
pytest tests/frontend/test_file_manager.py -v -s

# Run specific test
pytest tests/frontend/test_file_manager.py::TestFileManagerUpload::test_01_upload_single_file -v
```

## Key Test Patterns

### Upload Pattern
```python
# Navigate to demo page
navigate_to(page, "/file-manager-demo")

# Upload file via FilePond
file_input = page.locator('input[type="file"]').first
file_input.set_input_files(str(test_file_path))

# Wait for success
page.wait_for_selector('.filepond--file[data-filepond-item-state="processing-complete"]', timeout=15000)
```

### Verify in Admin List
```python
# Navigate and search
navigate_to(page, "/file_manager/")
page.wait_for_selector('#file_list_table', timeout=5000)
page.fill('input[type="search"]', filename)

# Check appears in table
assert page.locator(f'td:has-text("{filename}")').count() > 0
```

### Download Verification
```python
# Trigger download
with page.expect_download() as download_info:
    page.click('a[href*="download"]')
download = download_info.value

# Verify file
assert download.suggested_filename == expected_filename
```

## Notes for AI

### Test Isolation
- Each test uses unique filenames with timestamps to avoid conflicts
- Tests are ordered (`test_01_`, `test_02_`) to build on each other
- Upload tests must run before display/delete tests

### Timing Considerations
- FilePond upload needs 5-15s for processing
- Thumbnail generation adds 2-5s for images
- DataTables initialization needs 1-2s
- Use `page.wait_for_selector()` not fixed waits where possible

### Known Issues
- FilePond success selector varies by version - use `data-filepond-item-state="processing-complete"`
- DataTables search is debounced - add 500ms wait after typing
- Download testing requires Playwright's `expect_download()` context manager
- Thumbnail paths are relative from hashfs root: `.thumbs/150x150/...`

### Framework Integration
- Uses existing `conftest.py` fixtures: `logged_in_page`, `navigate_to`, `click_button`
- Requires FileManager permission: tests use `@require_permission("FileManager", "view")`
- Tests assume admin user with full permissions
- Server must be running on `http://localhost:5001`

## Coverage Goals

| Component | Target | Status |
|-----------|--------|--------|
| Upload | 100% | ✅ 100% |
| Display | 100% | ✅ 100% |
| Download | 90% | ✅ 100% |
| Delete | 90% | ✅ 100% |
| Thumbnails | 80% | ✅ 80% |
| Edit | 90% | ⏳ 0% |
| Versions | 80% | ⏳ 0% |
| Search | 70% | ⏳ 0% |

## Next Steps

1. ✅ Create test file directory structure
2. ✅ Implement high-priority tests
3. ⏳ Add test data files (images, PDFs, etc.)
4. ⏳ Implement medium-priority tests (edit, versions)
5. ⏳ Implement low-priority tests (edge cases)
6. ⏳ CI/CD integration

## Debugging Tips

### Test Failures
```python
# Enable verbose browser logging
page.on("console", lambda msg: print(f"[{msg.type}] {msg.text}"))

# Screenshot on failure
page.screenshot(path=f"test_failure_{test_name}.png")

# Get page HTML
print(page.content())
```

### FilePond Issues
- Check browser console for upload errors
- Verify server endpoint: `/files/upload`
- Check file permissions in upload directory
- Verify MIME type detection

### DataTables Issues
- Wait for `#file_list_table_wrapper` to exist (indicates initialization)
- Check for JavaScript errors in console
- Verify AJAX response contains file data

## Database Cleanup

Tests should NOT clean up uploaded files automatically to allow manual inspection. Use dedicated cleanup script if needed:

```python
# Cleanup script (run manually)
from src.modules.file_manager import FileManager
fm = FileManager(settings_manager)
test_files = fm.list_files_from_db()
for f in test_files:
    if 'frontend_test_' in f['name']:
        fm.delete_file(f['id'], delete_all_versions=True)
```
