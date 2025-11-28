# Test Files Directory

This directory contains test assets for file manager frontend tests.

## Files

Test files are created dynamically during test execution with unique timestamps to avoid conflicts:

- `frontend_test_image_*.jpg` - Minimal JPEG images (1x1 pixel)
- `frontend_test_text_*.txt` - Text files with test content
- `frontend_test_*.pdf` - PDF documents (optional)
- `frontend_test_*.png` - PNG images (optional)
- `frontend_test_*.zip` - Archive files (optional)

## Dynamic Creation

Most test files are created programmatically during test execution to ensure:
- Unique filenames (using timestamps)
- Minimal file size for fast tests
- No repository bloat from test data

## Cleanup

Test files are NOT automatically deleted after tests to allow manual inspection.
To clean up manually:

```python
# Delete all test files
from pathlib import Path
test_files_dir = Path("tests/frontend/test_files")
for f in test_files_dir.glob("frontend_test_*"):
    f.unlink()
```

## Downloaded Files

Downloaded files during tests are temporarily saved here with prefix `downloaded_*` and are cleaned up automatically after verification.
