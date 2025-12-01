"""
File Manager DisplayerItems - One-liner file upload and display components.

This module provides simplified DisplayerItems for file management:
- DisplayerItemFileUpload: FilePond-based upload with automatic field visibility
- DisplayerItemFileDisplay: File display with configurable actions (download, edit, history, delete)
"""

from typing import Dict, List, Optional

from .core import DisplayerCategory, DisplayerItems
from .items import DisplayerItem
from ..i18n.messages import ERROR_FILE_ID_OR_METADATA_REQUIRED


@DisplayerCategory.INPUT
class DisplayerItemFileUpload(DisplayerItem):
    """One-liner file upload using FilePond with optional tag/category controls.
    
    Upload endpoint is automatically handled by the framework (file_handler.upload).
    Fields are shown only when their value is None, hidden when provided.
    """
    
    def __init__(
        self,
        id: str,
        text: str = "Upload File",
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        group_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        accept_types: Optional[List[str]] = None,
        multiple: bool = False,
        existing_values: Optional[List[dict]] = None,
        simple: bool = False,
        upload_path: Optional[str] = None,
        rename_to: Optional[str] = None
    ) -> None:
        """Initialize a complete file upload widget with FilePond.
        
        Args:
            id: Unique identifier for the upload widget
            text: Label text for the upload field
            category: Fixed category (hidden if set, shown if None)
            subcategory: Fixed subcategory (hidden if set, shown if None)
            group_id: Fixed group_id for versioning (hidden if set, shown if None)
            tags: Fixed tags list (hidden if set, shown if None)
            accept_types: Accepted file types (e.g., ["image/*", ".pdf"])
            multiple: Allow multiple file uploads
            existing_values: Pre-existing file references
            simple: If True, use simple filesystem upload (no FileManager, no permissions)
            upload_path: For simple mode - relative path under website/assets/ (e.g., "images/users")
            rename_to: For simple mode - rename pattern (e.g., "{username}" uses session user)
        
        Examples:
            # Full control - user selects everything (FileManager mode)
            >>> upload = DisplayerItemFileUpload("my_upload", "Select File")
            
            # Fixed category - user selects tags and group
            >>> upload = DisplayerItemFileUpload(
            ...     "doc_upload", 
            ...     "Upload Document",
            ...     category="documents"
            ... )
            
            # Simple mode for avatar (filesystem, permissionless)
            >>> upload = DisplayerItemFileUpload(
            ...     "file_avatar",
            ...     "Upload Avatar",
            ...     simple=True,
            ...     upload_path="images/users",
            ...     rename_to="{username}",
            ...     accept_types=["image/*"]
            ... )
        """
        super().__init__(DisplayerItems.FILEUPLOAD)
        self.m_id = id
        self.m_text = text
        self.m_category = category
        self.m_subcategory = subcategory
        self.m_group_id = group_id
        self.m_tags = tags if tags is not None else []
        self.m_accept_types = accept_types
        self.m_multiple = multiple
        self.m_existing_values = existing_values if existing_values is not None else []
        self.m_simple = simple
        self.m_upload_path = upload_path
        self.m_rename_to = rename_to
    
    @classmethod
    def get_required_resources(cls) -> list:
        """File upload requires FilePond library.
        
        Returns:
            List of required resource paths.
        """
        return ['filepond']
    
    def display(self, container: list, parent_id: Optional[str] = None) -> None:
        """Add this item to a container view for template rendering.
        
        Args:
            container: The container list for items
            parent_id: Optional parent ID prefix
        """
        # Get file manager from global context
        from ...modules.file_manager import FileManager
        from ...modules import settings
        
        try:
            file_manager = FileManager(settings.settings_manager)
        except Exception:
            file_manager = None
        
        # Get list of existing groups if file_manager is available
        existing_groups = []
        if file_manager and file_manager.db_session:
            try:
                from sqlalchemy import text
                result = file_manager.db_session.execute(
                    text("SELECT DISTINCT group_id FROM file_groups WHERE group_id IS NOT NULL AND group_id != '' ORDER BY group_id")
                )
                existing_groups = [row[0] for row in result]
            except Exception:
                pass
        
        item = {
            "object": "item",
            "type": self.m_type.value,
            "id": f"{parent_id}.{self.m_id}" if parent_id else self.m_id,
            "text": self.m_text,
            "category": self.m_category,
            "subcategory": self.m_subcategory,
            "group_id": self.m_group_id,
            "tags": self.m_tags,
            "accept_types": self.m_accept_types,
            "multiple": self.m_multiple,
            "existing_values": self.m_existing_values,
            "file_manager": file_manager,
            "existing_groups": existing_groups,
            "simple": self.m_simple,
            "upload_path": self.m_upload_path,
            "rename_to": self.m_rename_to
        }
        
        container.append(item)
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample file upload.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(
            id="test_upload",
            text="Test Upload",
            category="test",
            tags=["demo"]
        )


@DisplayerCategory.DISPLAY
class DisplayerItemFileDisplay(DisplayerItem):
    """One-liner to display a file with action buttons.
    
    Automatically fetches file metadata and renders with preview, info, and actions.
    """
    
    def __init__(
        self,
        file_id: Optional[int] = None,
        file_metadata: Optional[Dict] = None,
        actions: Optional[List[str]] = None,
        compact: bool = False,
        version: Optional[int] = None
    ) -> None:
        """Initialize a file display with action buttons.
        
        Args:
            file_id: Database file ID (will auto-fetch metadata)
            file_metadata: Pre-fetched metadata dict (alternative to file_id)
            actions: List of action buttons to show (default: ["download"])
                     Options: "download", "edit", "history", "delete"
            compact: Display mode - False: full card, True: compact single line
            version: Specific version number to display (optional, for versioned files)
        
        Note:
            Either file_id OR file_metadata must be provided.
            If both are provided, file_metadata takes precedence.
        
        Examples:
            # Full file card with all actions
            >>> file_display = DisplayerItemFileDisplay(
            ...     file_id=123,
            ...     actions=["download", "edit", "history", "delete"]
            ... )
            
            # Compact download link
            >>> file_display = DisplayerItemFileDisplay(
            ...     file_id=123,
            ...     actions=["download"],
            ...     compact=True
            ... )
            
            # Full card with download + edit
            >>> file_display = DisplayerItemFileDisplay(
            ...     file_id=123,
            ...     actions=["download", "edit"]
            ... )
            
            # Using metadata dict instead of fetching
            >>> file_display = DisplayerItemFileDisplay(
            ...     file_metadata={"id": 123, "name": "doc.pdf", ...},
            ...     actions=["download"],
            ...     compact=True
            ... )
        """
        super().__init__(DisplayerItems.FILEDISPLAY)
        self.m_file_id = file_id
        self.m_file_metadata = file_metadata
        self.m_actions = actions if actions is not None else ["download"]
        self.m_compact = compact
        self.m_version = version
        
        # Validate that we have either file_id or file_metadata
        if file_id is None and file_metadata is None:
            raise ValueError(str(ERROR_FILE_ID_OR_METADATA_REQUIRED))
    
    def display(self, container: list, parent_id: Optional[str] = None) -> None:
        """Add this item to a container view for template rendering.
        
        Args:
            container: The container list for items
            parent_id: Optional parent ID prefix
        """
        # Get file manager from global context
        from ...modules.file_manager import FileManager
        from ...modules import settings
        
        try:
            file_manager = FileManager(settings.settings_manager)
        except Exception:
            file_manager = None
        
        item = {
            "object": "item",
            "type": self.m_type.value,
            "file_id": self.m_file_id,
            "file_metadata": self.m_file_metadata,
            "actions": self.m_actions,
            "compact": self.m_compact,
            "version": self.m_version,
            "file_manager": file_manager
        }
        
        container.append(item)
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample file display.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(
            file_metadata={
                "id": 1,
                "name": "test_document.pdf",
                "size": 1024000,
                "uploaded_at": "2025-11-18T10:30:00Z",
                "group_id": "test_group",
                "version": 1,
                "tags": ["test", "demo"]
            },
            actions=["download", "edit"],
            compact=False
        )
