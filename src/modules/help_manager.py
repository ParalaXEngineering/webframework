"""
Help Manager - Manages help content discovery, rendering, and configuration.

The help system supports three sources of help content:
1. Framework built-in help (src/help/)
2. Website-specific help (website/help/)
3. Plugin-contributed help (via PluginBase.get_help_content())

Help content is organized into sections, each containing multiple pages.
Sections can be enabled/disabled via the admin interface.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logging.warning("Markdown library not installed. Install with: pip install markdown")

from .log.logger_factory import get_logger

logger = get_logger("help_manager")


@dataclass
class HelpPage:
    """Represents a single help page."""
    
    id: str
    """Unique identifier (filename without extension)."""
    
    title: str
    """Display title extracted from markdown H1 or filename."""
    
    path: Path
    """Absolute path to the markdown file."""
    
    section: str
    """Section this page belongs to."""
    
    order: int = 100
    """Sort order within section (lower = first)."""
    
    description: str = ""
    """Short description extracted from first paragraph."""
    
    source: str = "website"
    """Source of this help page: 'framework', 'website', or plugin name."""


@dataclass 
class HelpSection:
    """Represents a section of help pages."""
    
    id: str
    """Unique identifier (folder name)."""
    
    title: str
    """Display title."""
    
    icon: str = "help-circle"
    """MDI icon name."""
    
    pages: List[HelpPage] = field(default_factory=list)
    """Pages in this section."""
    
    order: int = 100
    """Sort order (lower = first)."""
    
    source: str = "website"
    """Source: 'framework', 'website', or plugin name."""
    
    enabled: bool = True
    """Whether this section is visible to users."""
    
    requires_feature: Optional[str] = None
    """Feature flag that must be enabled for this section to show."""
    

class HelpManager:
    """
    Manages help content discovery, rendering, and section configuration.
    
    The manager scans for markdown files in configured directories,
    extracts metadata, and provides methods to retrieve and render content.
    
    Attributes:
        sections: Dict of section_id -> HelpSection
        settings_manager: Reference to settings manager for persistence
    """
    
    # Configuration keys for section enabled/disabled state
    CONFIG_CATEGORY = "help"
    CONFIG_KEY = "help.enabled_sections"
    
    # Metadata comment pattern for extracting page metadata
    # Example: <!-- help: order=10, requires=authentication -->
    METADATA_PATTERN = re.compile(
        r'<!--\s*help:\s*(.+?)\s*-->',
        re.IGNORECASE | re.DOTALL
    )
    
    def __init__(self, app_path: str, settings_manager: Optional[Any] = None):
        """
        Initialize the help manager.
        
        Args:
            app_path: Path to the application root
            settings_manager: Optional settings manager for persisting config
        """
        self.app_path = Path(app_path)
        self.settings_manager = settings_manager
        self.sections: Dict[str, HelpSection] = {}
        self._site_conf = None
        
        # Markdown renderer configuration
        self.md_extensions = [
            'tables',
            'fenced_code',
            'codehilite',
            'toc',
            'attr_list',
            'md_in_html',
        ]
        
    def set_site_conf(self, site_conf: Any) -> None:
        """Set reference to site configuration for feature flag checking."""
        self._site_conf = site_conf
        
    def discover_content(self) -> None:
        """
        Scan all help directories and discover available content.
        
        This method:
        1. Scans website/help/ for site-specific help
        2. Loads section enabled/disabled state from settings
        """
        
        self.sections.clear()
        
        # Primary location: website/help/
        website_help_path = self.app_path / "website" / "help"
        
        if website_help_path.exists():
            self._scan_help_directory(website_help_path, source="website")
        
        # Load enabled/disabled state from settings
        self._load_section_config()
        
        # Sort sections and pages
        self._sort_content()
    
    def register_plugin_help(self, plugin_name: str, help_content: Dict[str, Any]) -> None:
        """
        Register help content from a plugin.
        
        Plugins can provide help content by implementing get_help_content()
        which returns a dict with:
        - sections: List of section definitions
        - pages: List of page definitions with 'section' field
        
        Args:
            plugin_name: Name of the plugin providing content
            help_content: Dict with 'sections' and/or 'pages' keys
        """        
        # Scan plugin's help directory if it exists
        # Expected location: submodules/{plugin_name}/help/
        plugin_help_path = self.app_path / "submodules" / plugin_name / "help"
        
        if plugin_help_path.exists():
            self._scan_help_directory(plugin_help_path, source=plugin_name)
        
        # Register any dynamically defined sections from help_content dict
        if not help_content:
            help_content = {}
            
        sections = help_content.get("sections", [])
        
        for section_def in sections:
            section_id = section_def.get("id", plugin_name)
            if section_id not in self.sections:
                self.sections[section_id] = HelpSection(
                    id=section_id,
                    title=section_def.get("title", plugin_name.title()),
                    icon=section_def.get("icon", "puzzle"),
                    order=section_def.get("order", 100),
                    source=plugin_name,
                    requires_feature=section_def.get("requires_feature"),
                )
        
        self._sort_content()
    
    def _scan_help_directory(self, base_path: Path, source: str = "website") -> None:
        """
        Scan a directory for help content organized in sections.
        
        Expected structure:
            base_path/
                section1/
                    _section.json  (optional metadata)
                    page1.md
                    page2.md
                section2/
                    ...
        
        Args:
            base_path: Directory to scan
            source: Source identifier for discovered content
        """
        logger.info(f"  Scanning help directory: {base_path} (source: {source})")
        
        if not base_path.exists():
            logger.warning(f"  Base path does not exist: {base_path}")
            return
        
        items = list(base_path.iterdir())
        
        for item in items:
            
            if item.is_dir() and not item.name.startswith('_'):
                section_id = item.name
                
                # Load section metadata if available
                section_meta_path = item / "_section.json"
                section_meta = {}
                if section_meta_path.exists():
                    try:
                        with open(section_meta_path, 'r', encoding='utf-8') as f:
                            section_meta = json.load(f)
                    except (json.JSONDecodeError, IOError) as e:
                        logger.warning(f"Failed to load section metadata from {section_meta_path}: {e}")
                
                # Create or update section
                if section_id not in self.sections:
                    self.sections[section_id] = HelpSection(
                        id=section_id,
                        title=section_meta.get("title", self._id_to_title(section_id)),
                        icon=section_meta.get("icon", "help-circle"),
                        order=section_meta.get("order", 100),
                        source=source,
                        requires_feature=section_meta.get("requires_feature"),
                    )
                
                # Scan for markdown files
                md_files = list(item.glob("*.md"))
                
                for md_file in md_files:
                    if md_file.name.startswith('_'):
                        logger.info(f"    Skipping file (starts with _): {md_file.name}")
                        continue
                    page = self._parse_help_page(md_file, section_id, source)
                    if page:
                        self.sections[section_id].pages.append(page)
    
    def _parse_help_page(self, file_path: Path, section_id: str, source: str) -> Optional[HelpPage]:
        """
        Parse a markdown file and extract help page metadata.
        
        Args:
            file_path: Path to the markdown file
            section_id: Section this page belongs to
            source: Source identifier
            
        Returns:
            HelpPage instance or None if parsing failed
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except IOError as e:
            logger.error(f"Failed to read help file {file_path}: {e}")
            return None
        
        page_id = file_path.stem
        
        # Extract title from first H1
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else self._id_to_title(page_id)
        
        # Extract description from first non-heading paragraph
        desc_match = re.search(r'^(?!#)(.+?)(?=\n\n|\n#|$)', content, re.MULTILINE | re.DOTALL)
        description = ""
        if desc_match:
            desc_text = desc_match.group(1).strip()
            # Remove any leading/trailing newlines and take first 200 chars
            description = ' '.join(desc_text.split())[:200]
        
        # Extract metadata from HTML comment
        order = 100
        meta_match = self.METADATA_PATTERN.search(content)
        if meta_match:
            meta_str = meta_match.group(1)
            # Parse key=value pairs
            for pair in meta_str.split(','):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    if key == 'order':
                        try:
                            order = int(value)
                        except ValueError:
                            pass
        
        return HelpPage(
            id=page_id,
            title=title,
            path=file_path,
            section=section_id,
            order=order,
            description=description,
            source=source,
        )
    
    def _id_to_title(self, id_str: str) -> str:
        """Convert an ID string to a display title."""
        # Replace underscores/hyphens with spaces, capitalize words
        return id_str.replace('_', ' ').replace('-', ' ').title()
    
    def _sort_content(self) -> None:
        """Sort sections and pages by order."""
        # Sort sections
        self.sections = dict(
            sorted(self.sections.items(), key=lambda x: (x[1].order, x[1].title))
        )
        # Sort pages within each section
        for section in self.sections.values():
            section.pages.sort(key=lambda p: (p.order, p.title))
    
    def _load_section_config(self) -> None:
        """Load section enabled/disabled state from settings."""
        if not self.settings_manager:
            return
            
        try:
            # Get the enabled_sections dict from help category
            config = self.settings_manager.get_setting(self.CONFIG_KEY)
            
            if config:
                for section_id, section in self.sections.items():
                    if section_id in config:
                        section.enabled = config[section_id]
        except Exception as e:
            logger.warning(f"Failed to load help section config: {e}")
    
    def save_section_config(self, section_states: Dict[str, bool]) -> bool:
        """
        Save section enabled/disabled state to settings.
        
        Args:
            section_states: Dict of section_id -> enabled (boolean)
            
        Returns:
            True if saved successfully
        """
        if not self.settings_manager:
            logger.warning("No settings manager available, cannot save help config")
            return False
            
        try:
            # Ensure the help category exists in settings
            all_settings = self.settings_manager.get_all_settings()
            if self.CONFIG_CATEGORY not in all_settings:
                # Create the help category
                all_settings[self.CONFIG_CATEGORY] = {
                    "friendly": "Help System",
                    "enabled_sections": {
                        "friendly": "Enabled Sections",
                        "type": "dict",
                        "value": {},
                        "persistent": True
                    }
                }
                self.settings_manager.storage._settings = all_settings
                self.settings_manager.save()
            
            # Now set the value
            self.settings_manager.set_setting(self.CONFIG_KEY, section_states)
            
            # Update in-memory state
            for section_id, enabled in section_states.items():
                if section_id in self.sections:
                    self.sections[section_id].enabled = enabled
                    
            return True
        except Exception as e:
            logger.error(f"Failed to save help section config: {e}")
            return False
    
    def get_visible_sections(self) -> List[HelpSection]:
        """
        Get all sections that should be visible to users.
        
        This filters out:
        - Disabled sections
        - Sections requiring features that aren't enabled
        
        Returns:
            List of visible HelpSection instances
        """
        visible = []
        for section in self.sections.values():
            if not section.enabled:
                continue
                
            # Check feature flag requirement
            if section.requires_feature and self._site_conf:
                flag_name = f"m_enable_{section.requires_feature}"
                if hasattr(self._site_conf, flag_name):
                    if not getattr(self._site_conf, flag_name):
                        continue
                        
            visible.append(section)
            
        return visible
    
    def get_all_sections(self) -> List[HelpSection]:
        """Get all sections (for admin interface)."""
        return list(self.sections.values())
    
    def get_section(self, section_id: str) -> Optional[HelpSection]:
        """Get a specific section by ID."""
        return self.sections.get(section_id)
    
    def get_page(self, section_id: str, page_id: str) -> Optional[HelpPage]:
        """Get a specific page by section and page ID."""
        section = self.sections.get(section_id)
        if not section:
            return None
        for page in section.pages:
            if page.id == page_id:
                return page
        return None
    
    def render_page(self, page: HelpPage) -> Tuple[str, Dict[str, Any]]:
        """
        Render a help page's markdown content to HTML.
        
        Args:
            page: HelpPage to render
            
        Returns:
            Tuple of (html_content, metadata_dict)
        """
        if not MARKDOWN_AVAILABLE:
            return "<p>Markdown library not installed.</p>", {}
            
        try:
            content = page.path.read_text(encoding='utf-8')
        except IOError as e:
            logger.error(f"Failed to read help file {page.path}: {e}")
            return f"<p>Error loading help content: {e}</p>", {}
        
        # Remove metadata comment before rendering
        content = self.METADATA_PATTERN.sub('', content)
        
        # Create markdown instance with extensions
        md = markdown.Markdown(extensions=self.md_extensions)
        html = md.convert(content)
        
        # Extract TOC if available
        toc = getattr(md, 'toc', '')
        
        return html, {"toc": toc}
    
    def get_page_content(self, section_id: str, page_id: str) -> Optional[Tuple[str, HelpPage, Dict[str, Any]]]:
        """
        Get rendered content for a help page.
        
        Args:
            section_id: Section identifier
            page_id: Page identifier
            
        Returns:
            Tuple of (html_content, HelpPage, metadata) or None if not found
        """
        page = self.get_page(section_id, page_id)
        if not page:
            return None
            
        html, metadata = self.render_page(page)
        return html, page, metadata
