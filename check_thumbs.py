#!/usr/bin/env python
"""Quick script to check thumbnail status in database."""
from src.modules.file_manager import FileManager
from src.modules import settings
import json

fm = FileManager(settings.settings_manager)
files = fm.list_files_from_db(limit=5)

print(f"Found {len(files)} files in database\n")
for f in files:
    print(f"File: {f['name']}")
    print(f"  Has thumb_150x150: {'thumb_150x150' in f}")
    print(f"  Has thumb_300x300: {'thumb_300x300' in f}")
    if 'thumb_150x150' in f:
        print(f"  Thumb path: {f['thumb_150x150']}")
    print(f"  All keys: {list(f.keys())}")
    print()
