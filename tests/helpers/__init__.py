"""
Test Helpers Module

Consolidated helper functions for frontend tests.
Extracted from test_sea_system_data.py (source of truth).

Usage:
    from tests.helpers import create_linkable_manifest, add_atomic_attribute, create_module
    from tests.helpers.manifest_helpers import create_non_linkable_manifest
"""

from tests.helpers.manifest_helpers import (
    create_manifest,
    create_linkable_manifest,
    create_non_linkable_manifest,
    delete_manifest,
    enable_manifest_flag,
    enable_siblings_on_manifest,
    enable_cascading_on_manifest,
)

from tests.helpers.attribute_helpers import (
    add_atomic_attribute,
    add_manifest_attribute,
    add_linkable_attribute,
    add_select_attribute,
    add_file_attribute,
    add_auto_increment_attribute,
    edit_inid_attribute_to_manifest,
    edit_attribute,
    delete_attribute,
)

from tests.helpers.module_helpers import (
    create_module,
    delete_module,
    set_module_attribute_options,
    set_module_auto_increment_pattern,
    configure_target_module,
    set_module_default,
    save_attribute_value,
)

from tests.helpers.tracker_helpers import (
    create_tracker,
    create_auto_increment_tracker,
    create_simple_tracker,
    edit_tracker_field,
    upload_file_to_tracker,
    add_to_tracker_array,
    remove_from_tracker_array,
    delete_tracker,
    add_sibling_relationship,
    set_attribute_and_cascade,
    verify_tracker_exists,
    verify_tracker_attribute,
    add_embedded_item,
)

from tests.helpers.backup_helpers import (
    create_test_backup,
    restore_test_backup,
    list_test_backups,
    get_backup_path,
    create_backup_via_ui,
    restore_backup_via_ui,
    delete_backup_via_ui,
)

__all__ = [
    # Manifest helpers
    'create_manifest',
    'create_linkable_manifest',
    'create_non_linkable_manifest',
    'delete_manifest',
    'enable_manifest_flag',
    'enable_siblings_on_manifest',
    'enable_cascading_on_manifest',
    # Attribute helpers
    'add_atomic_attribute',
    'add_manifest_attribute',
    'add_linkable_attribute',
    'add_select_attribute',
    'add_file_attribute',
    'add_auto_increment_attribute',
    'edit_inid_attribute_to_manifest',
    'edit_attribute',
    'delete_attribute',
    # Module helpers
    'create_module',
    'delete_module',
    'set_module_attribute_options',
    'set_module_auto_increment_pattern',
    'configure_target_module',
    'set_module_default',
    'save_attribute_value',
    # Tracker helpers
    'create_tracker',
    'create_auto_increment_tracker',
    'create_simple_tracker',
    'edit_tracker_field',
    'upload_file_to_tracker',
    'add_to_tracker_array',
    'remove_from_tracker_array',
    'delete_tracker',
    'add_sibling_relationship',
    'set_attribute_and_cascade',
    'verify_tracker_exists',
    'verify_tracker_attribute',
    'add_embedded_item',
    # Backup helpers
    'create_test_backup',
    'restore_test_backup',
    'list_test_backups',
    'get_backup_path',
    'create_backup_via_ui',
    'restore_backup_via_ui',
    'delete_backup_via_ui',
    # Workarounds
    'fix_module_ref_for_attribute',
]
