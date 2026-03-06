"""
Help blueprint - Provides public help pages and admin configuration.

Uses the framework's Displayer system for consistent UI rendering.

Routes:
    /help/                     - Help index (public)
    /help/<section>/           - Section index (public)
    /help/<section>/<page>     - Individual page (public)
    /help/admin                - Admin configuration (requires admin)
"""

from flask import Blueprint, request, flash, redirect, url_for, render_template, send_from_directory, abort
from collections import OrderedDict

from ..modules import displayer
from ..modules.displayer import (
    Displayer,
    DisplayerLayout,
    Layouts,
    BSstyle,
    DisplayerItemText,
    DisplayerItemBadge,
    DisplayerItemButton,
    DisplayerItemAlert,
    DisplayerItemCard,
)
from ..modules.app_context import app_context
from ..modules.auth import require_admin
from ..modules.utilities import util_post_to_json
from ..modules.i18n.messages import (
    MSG_SETTINGS_SAVED,
    ERROR_SAVING_SETTINGS,
)

bp = Blueprint(
    'help',
    __name__,
    url_prefix='/help'
)

# =============================================================================
# Constants
# =============================================================================

TEXT_HELP = "Help"
TEXT_HELP_CENTER = "Help Center"
TEXT_HELP_CONFIGURATION = "Help Configuration"
TEXT_SECTION = "Section"
TEXT_ARTICLES = "Articles"
TEXT_SOURCE = "Source"
TEXT_ENABLED = "Enabled"
TEXT_REQUIRES_FEATURE = "Requires Feature"
TEXT_ACTIONS = "Actions"
TEXT_NO_HELP_CONTENT = "No help content available"
TEXT_NO_ARTICLES = "No articles in this section"
TEXT_BACK_TO_HELP = "Back to Help Center"
TEXT_BACK_TO_SECTION = "Back to Section"
TEXT_ON_THIS_PAGE = "On This Page"
TEXT_WELCOME_HELP = "Welcome to the help center. Select a topic below to get started."
TEXT_ENABLE_DISABLE_INFO = "Enable or disable help sections. Disabled sections will not appear in the help center."
TEXT_CREATE_HELP_INFO = "Create help content in website/help/ with markdown files organized in sections."


# =============================================================================
# Helper Functions
# =============================================================================

def _get_help_manager():
    """Get the help manager from app context."""
    return app_context.help_manager


def _render_error_page(message: str, status_code: int = 404):
    """Render an error page using Displayer."""
    disp = Displayer()
    disp.add_generic(TEXT_HELP, display=False)
    disp.set_title(TEXT_HELP_CENTER)
    disp.add_breadcrumb(TEXT_HELP, "help.index", [])
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(
        DisplayerItemAlert(f"<i class='mdi mdi-alert-circle'></i> {message}", BSstyle.WARNING)
    )
    
    return render_template("base_content.j2", content=disp.display()), status_code


# =============================================================================
# Public Routes
# =============================================================================

@bp.route('/')
def index():
    """Display help index with all visible sections."""
    help_manager = _get_help_manager()
    if not help_manager:
        return _render_error_page("Help system not available", 503)
    
    sections = help_manager.get_visible_sections()
    
    disp = Displayer()
    disp.add_generic(TEXT_HELP, display=False)
    disp.set_title(TEXT_HELP_CENTER)
    disp.add_breadcrumb(TEXT_HELP, "help.index", [])
    
    if not sections:
        # No content available
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(
            DisplayerItemAlert(
                f"<div class='text-center py-4'>"
                f"<i class='mdi mdi-book-open-variant' style='font-size: 4rem;'></i>"
                f"<h5 class='mt-3'>{TEXT_NO_HELP_CONTENT}</h5>"
                f"</div>",
                BSstyle.NONE
            )
        )
        return render_template("base_content.j2", content=disp.display())
    
    # Welcome message
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(TEXT_WELCOME_HELP))

    # Group sections by top-level group metadata
    grouped_sections = OrderedDict()
    sorted_sections = sorted(
        sections,
        key=lambda s: (getattr(s, 'group_order', 100), getattr(s, 'group', 'General'), s.order, s.title)
    )
    for section in sorted_sections:
        group_name = getattr(section, 'group', 'General') or 'General'
        grouped_sections.setdefault(group_name, []).append(section)

    for group_name, group_sections in grouped_sections.items():
        # Group title (section-like heading)
        group_layout_id = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(
            DisplayerItemAlert(
                f"<h2 class='mb-3 mt-4'><i class='mdi mdi-folder-outline text-primary me-2'></i>{group_name}</h2>",
                BSstyle.NONE
            ),
            column=0,
            layout_id=group_layout_id
        )

        cols_per_row = 3 if len(group_sections) >= 3 else len(group_sections)
        col_width = 12 // cols_per_row if cols_per_row > 0 else 12

        layout_id = disp.add_master_layout(DisplayerLayout(
            Layouts.VERTICAL,
            [col_width] * min(len(group_sections), cols_per_row)
        ))

        for idx, section in enumerate(group_sections):
            col = idx % cols_per_row

            page_count = len(section.pages)
            page_list = "<ul class='list-unstyled mb-0'>"
            for page in section.pages:
                page_url = url_for('help.page', section_id=section.id, page_id=page.id)
                page_list += f"<li class='mb-1'><a href='{page_url}'><i class='mdi mdi-file-document-outline text-primary me-1'></i>{page.title}</a></li>"

            if not section.pages:
                page_list += "<li><em class='text-muted'>No articles yet</em></li>"

            page_list += "</ul>"

            card = DisplayerItemCard(
                id=f"section_{section.id}",
                title=section.title,
                subtitle=f"{page_count} article{'s' if page_count != 1 else ''}",
                icon=section.icon,
                header_color=BSstyle.PRIMARY,
                body=page_list
            )

            disp.add_display_item(card, column=col, layout_id=layout_id)

            if (idx + 1) % cols_per_row == 0 and idx + 1 < len(group_sections):
                remaining = len(group_sections) - (idx + 1)
                next_cols = min(remaining, cols_per_row)
                layout_id = disp.add_master_layout(DisplayerLayout(
                    Layouts.VERTICAL,
                    [col_width] * next_cols
                ))
    
    return render_template("base_content.j2", content=disp.display())


@bp.route('/<section_id>/images/<path:filename>')
def serve_image(section_id: str, filename: str):
    """Serve images from help section directories."""
    help_manager = _get_help_manager()
    if not help_manager:
        abort(404)
    
    # Find the section to get its source
    section = help_manager.sections.get(section_id)
    if not section:
        abort(404)
    
    # Determine the base path for this section's images
    from pathlib import Path
    app_path = Path(help_manager.app_path)
    
    # Check in website/help first
    image_path = app_path / "website" / "help" / section_id / "images"
    if image_path.exists() and (image_path / filename).exists():
        return send_from_directory(str(image_path), filename)
    
    # Check in plugin help directories
    plugin_path = app_path / "submodules" / section.source / "help" / section_id / "images"
    if plugin_path.exists() and (plugin_path / filename).exists():
        return send_from_directory(str(plugin_path), filename)
    
    abort(404)


@bp.route('/<section_id>/<page_id>')
def page(section_id: str, page_id: str):
    """Display an individual help page."""
    help_manager = _get_help_manager()
    if not help_manager:
        return _render_error_page("Help system not available", 503)
    
    section = help_manager.get_section(section_id)
    if not section or not section.enabled:
        return _render_error_page(f"Help section '{section_id}' not found", 404)
    
    result = help_manager.get_page_content(section_id, page_id)
    if not result:
        return _render_error_page(f"Help page '{page_id}' not found", 404)
    
    html_content, page_obj, metadata = result
    
    # Find prev/next pages
    prev_page = None
    next_page = None
    pages = section.pages
    for i, p in enumerate(pages):
        if p.id == page_id:
            if i > 0:
                prev_page = pages[i - 1]
            if i < len(pages) - 1:
                next_page = pages[i + 1]
            break
    
    disp = Displayer()
    disp.add_generic(TEXT_HELP, display=False)
    disp.set_title(page_obj.title)
    disp.add_breadcrumb(TEXT_HELP, "help.index", [])
    disp.add_breadcrumb(page_obj.title, "help.page", [f"section_id={section_id}", f"page_id={page_id}"])
    
    toc = metadata.get('toc', '')
    
    # CSS for markdown content styling
    help_css = """
    <style>
        .help-content { line-height: 1.7; }
        .help-content h1:first-of-type { display: none; }
        .help-content h1 { font-size: 2rem; margin-bottom: 1rem; border-bottom: 2px solid var(--bs-primary); padding-bottom: 0.5rem; }
        .help-content h2 { font-size: 1.5rem; margin-top: 2rem; margin-bottom: 1rem; color: var(--bs-primary); }
        .help-content h3 { font-size: 1.25rem; margin-top: 1.5rem; margin-bottom: 0.75rem; }
        .help-content pre { background-color: var(--bs-gray-100); padding: 1rem; border-radius: 0.375rem; overflow-x: auto; }
        .help-content code { background-color: var(--bs-gray-100); padding: 0.125rem 0.375rem; border-radius: 0.25rem; font-size: 0.875em; }
        .help-content pre code { background-color: transparent; padding: 0; }
        .help-content blockquote { border-left: 4px solid var(--bs-primary); padding-left: 1rem; margin-left: 0; color: var(--bs-secondary); }
        .help-content img { max-width: 100%; height: auto; border-radius: 0.375rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 1rem 0; }
        .help-content table { width: 100%; margin: 1rem 0; border-collapse: collapse; }
        .help-content th, .help-content td { border: 1px solid var(--bs-gray-300); padding: 0.5rem; }
        .help-content th { background-color: var(--bs-gray-100); }
        .help-content .admonition { padding: 0.75rem 1rem; border-radius: 0.375rem; margin: 1rem 0; border-left: 4px solid var(--bs-info); background-color: rgba(var(--bs-info-rgb), 0.1); }
        .help-content .admonition.note { border-color: var(--bs-info); background-color: rgba(var(--bs-info-rgb), 0.1); }
        .help-content .admonition.warning { border-color: var(--bs-warning); background-color: rgba(var(--bs-warning-rgb), 0.1); }
        .help-content .admonition.danger, .help-content .admonition.error { border-color: var(--bs-danger); background-color: rgba(var(--bs-danger-rgb), 0.1); }
        .help-content .admonition.tip, .help-content .admonition.hint { border-color: var(--bs-success); background-color: rgba(var(--bs-success-rgb), 0.1); }
        .help-content .admonition-title { font-weight: 600; margin-bottom: 0.25rem; text-transform: capitalize; }
    </style>
    """
    
    # Layout: main content + optional TOC sidebar
    if toc:
        layout_id = disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, [9, 3]))
        
        # Main content - wrap in div for styling
        content_html = f"{help_css}<div class='help-content'>{html_content}</div>"
        disp.add_display_item(DisplayerItemAlert(content_html, BSstyle.NONE), column=0, layout_id=layout_id)
        
        # TOC sidebar
        toc_html = f"""
        <div class="card sticky-top" style="top: 1rem;">
            <div class="card-header">
                <h6 class="mb-0"><i class="mdi mdi-format-list-bulleted me-1"></i>{TEXT_ON_THIS_PAGE}</h6>
            </div>
            <div class="card-body small">
                {toc}
            </div>
        </div>
        """
        disp.add_display_item(DisplayerItemAlert(toc_html, BSstyle.NONE), column=1, layout_id=layout_id)
    else:
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        content_html = f"{help_css}<div class='help-content'>{html_content}</div>"
        disp.add_display_item(DisplayerItemAlert(content_html, BSstyle.NONE))
    
    # Navigation buttons
    nav_layout_id = disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, [6, 6]))
    
    # Previous button
    if prev_page:
        disp.add_display_item(
            DisplayerItemButton(
                id="btn_prev_page",
                text=prev_page.title,
                icon="arrow-left",
                link=url_for('help.page', section_id=section.id, page_id=prev_page.id),
                color=BSstyle.PRIMARY
            ),
            column=0, layout_id=nav_layout_id
        )
    
    # Next button  
    if next_page:
        disp.add_display_item(
            DisplayerItemButton(
                id="btn_next_page",
                text=next_page.title,
                icon="arrow-right",
                link=url_for('help.page', section_id=section.id, page_id=next_page.id),
                color=BSstyle.PRIMARY
            ),
            column=1, layout_id=nav_layout_id
        )
    
    # Back to help center button
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_back_help",
            text=TEXT_BACK_TO_HELP,
            icon="arrow-left",
            link=url_for('help.index'),
            color=BSstyle.SECONDARY
        )
    )
    
    return render_template("base_content.j2", content=disp.display())


# =============================================================================
# Admin Routes
# =============================================================================

@bp.route('/admin', methods=['GET', 'POST'])
@require_admin()
def admin():
    """Admin page to configure help sections."""
    help_manager = _get_help_manager()
    if not help_manager:
        return _render_error_page("Help system not available", 503)
    
    if request.method == 'POST':
        # Get all section IDs and their enabled state
        # util_post_to_json transforms "section_id": "on" into {"section": ["id1", "id2", ...]}
        data = util_post_to_json(request.form.to_dict())
        
        # Get enabled section IDs from the transformed data
        enabled_sections = data.get('section', [])
        if not isinstance(enabled_sections, list):
            enabled_sections = [enabled_sections] if enabled_sections else []
        
        # Create section_states dict with all sections
        section_states = {}
        for section in help_manager.get_all_sections():
            section_states[section.id] = section.id in enabled_sections
        
        if help_manager.save_section_config(section_states):
            flash(str(MSG_SETTINGS_SAVED), 'success')
        else:
            flash(str(ERROR_SAVING_SETTINGS), 'danger')
        
        return redirect(url_for('help.admin'))
    
    sections = help_manager.get_all_sections()
    
    disp = Displayer()
    disp.add_generic(TEXT_HELP, display=False)
    disp.set_title(TEXT_HELP_CONFIGURATION)
    disp.add_breadcrumb(TEXT_HELP, "help.index", [])
    disp.add_breadcrumb(TEXT_HELP_CONFIGURATION, "help.admin", [])
    
    # Two column layout: config table + info panel
    main_layout_id = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [8, 4]))
    
    # Left column: Configuration form
    if sections:
        # Wrap everything in form
        disp.add_display_item(
            DisplayerItemAlert('<form method="POST" action="">', BSstyle.NONE),
            column=0, layout_id=main_layout_id
        )
        
        # Info text
        info_html = f"<p class='text-muted mb-3'>{TEXT_ENABLE_DISABLE_INFO}</p>"
        disp.add_display_item(DisplayerItemAlert(info_html, BSstyle.NONE), column=0, layout_id=main_layout_id)
        
        # Create table layout for sections
        table_layout = DisplayerLayout(
            Layouts.TABLE,
            columns=["Enabled", "Section", "Source", "Articles", "Feature Requirement"]
        )
        table_id = disp.add_slave_layout(table_layout, column=0, layout_id=main_layout_id)
        
        for idx, section in enumerate(sections):
            checked = "checked" if section.enabled else ""
            
            # Source badge
            if section.source == 'website':
                source_badge_item = DisplayerItemBadge("Website", BSstyle.INFO)
            elif section.source == 'framework':
                source_badge_item = DisplayerItemBadge("Framework", BSstyle.SECONDARY)
            else:
                source_badge_item = DisplayerItemBadge(f"Plugin: {section.source}", BSstyle.SUCCESS)
            
            # Feature requirement
            feature_req = f"<code>{section.requires_feature}</code>" if section.requires_feature else '<span class="text-muted">—</span>'
            
            # Checkbox cell
            checkbox_html = f'''
            <div class="form-check">
                <input type="checkbox" class="form-check-input" name="section_{section.id}" id="section_{section.id}" {checked}>
            </div>
            '''
            disp.add_display_item(DisplayerItemAlert(checkbox_html, BSstyle.NONE), column=0, layout_id=table_id, line=idx)
            
            # Section name cell
            section_html = f'''
            <label for="section_{section.id}" class="mb-0 d-flex align-items-center">
                <i class="mdi mdi-{section.icon} text-primary me-2"></i>
                <strong>{section.title}</strong>
            </label>
            <br><small class="text-muted">{section.id}</small>
            '''
            disp.add_display_item(DisplayerItemAlert(section_html, BSstyle.NONE), column=1, layout_id=table_id, line=idx)
            
            # Source cell
            disp.add_display_item(source_badge_item, column=2, layout_id=table_id, line=idx)
            
            # Articles count cell
            articles_badge = DisplayerItemBadge(str(len(section.pages)), BSstyle.LIGHT)
            disp.add_display_item(articles_badge, column=3, layout_id=table_id, line=idx)
            
            # Feature requirement cell
            disp.add_display_item(DisplayerItemAlert(feature_req, BSstyle.NONE), column=4, layout_id=table_id, line=idx)
        
        # Close form tag
        disp.add_display_item(DisplayerItemAlert('</form>', BSstyle.NONE), column=0, layout_id=main_layout_id)
        
        # Buttons after table
        btn_layout = disp.add_slave_layout(DisplayerLayout(Layouts.HORIZONTAL, [6, 6]), column=0, layout_id=main_layout_id)
        disp.add_display_item(
            DisplayerItemButton(
                id="btn_save_config",
                text="Save Configuration",
                icon="content-save",
                color=BSstyle.PRIMARY
            ),
            column=0, layout_id=btn_layout
        )
        disp.add_display_item(
            DisplayerItemButton(
                id="btn_view_help",
                text="View Help Center",
                icon="eye",
                link=url_for('help.index'),
                color=BSstyle.SECONDARY
            ),
            column=1, layout_id=btn_layout
        )
    else:
        # No sections
        empty_html = f"""
        <div class="text-center py-5">
            <i class="mdi mdi-folder-open-outline text-muted" style="font-size: 4rem;"></i>
            <h5 class="mt-3 text-muted">No Help Sections Found</h5>
            <p class="text-muted">{TEXT_CREATE_HELP_INFO}</p>
        </div>
        """
        disp.add_display_item(DisplayerItemAlert(empty_html, BSstyle.NONE), column=0, layout_id=main_layout_id)
    
    # Right column: Help/info panel
    info_panel_html = """
    <div class="card">
        <div class="card-header">
            <h5 class="card-title mb-0"><i class="mdi mdi-information me-2"></i>Help System Guide</h5>
        </div>
        <div class="card-body">
            <h6>Creating Help Content</h6>
            <p class="small text-muted">Add markdown files to <code>website/help/</code> organized in folders (sections).</p>
            
            <h6>Directory Structure</h6>
            <pre class="small bg-light p-2 rounded"><code>website/help/
├── getting-started/
│   ├── _section.json
│   ├── introduction.md
│   └── first-steps.md
└── user-guide/
    └── basics.md</code></pre>
            
            <h6>Section Metadata</h6>
            <p class="small text-muted">Create <code>_section.json</code> in a folder to customize:</p>
            <pre class="small bg-light p-2 rounded"><code>{
  "title": "Getting Started",
  "icon": "rocket-launch",
    "section_group": "Generic Usage",
    "section_group_order": 1,
  "order": 10,
  "requires_feature": "authentication"
}</code></pre>
            
            <h6>Page Metadata</h6>
            <p class="small text-muted">Add metadata comments to markdown files:</p>
            <pre class="small bg-light p-2 rounded"><code>&lt;!-- help: order=10 --&gt;
# Page Title
Content here...</code></pre>
        </div>
    </div>
    """
    disp.add_display_item(DisplayerItemAlert(info_panel_html, BSstyle.NONE), column=1, layout_id=main_layout_id)
    
    return render_template("base_content.j2", content=disp.display())
