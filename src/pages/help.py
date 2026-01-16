"""
Help blueprint - Provides public help pages and admin configuration.

Uses the framework's Displayer system for consistent UI rendering.

Routes:
    /help/                     - Help index (public)
    /help/<section>/           - Section index (public)
    /help/<section>/<page>     - Individual page (public)
    /help/admin                - Admin configuration (requires admin)
"""

from flask import Blueprint, request, flash, redirect, url_for, render_template

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
)
from ..modules.app_context import app_context
from ..modules.auth import require_admin
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
    
    # Section cards - use a grid layout
    cols_per_row = 3 if len(sections) >= 3 else len(sections)
    col_width = 12 // cols_per_row if cols_per_row > 0 else 12
    
    layout_id = disp.add_master_layout(DisplayerLayout(
        Layouts.HORIZONTAL, 
        [col_width] * min(len(sections), cols_per_row)
    ))
    
    for idx, section in enumerate(sections):
        col = idx % cols_per_row
        
        # Build section card content
        page_count = len(section.pages)
        page_list = ""
        for page in section.pages[:3]:
            page_url = url_for('help.page', section_id=section.id, page_id=page.id)
            page_list += f"<li class='mb-1'><a href='{page_url}'><i class='mdi mdi-file-document-outline me-1'></i>{page.title}</a></li>"
        
        if page_count > 3:
            section_url = url_for('help.section_index', section_id=section.id)
            page_list += f"<li><a href='{section_url}' class='text-primary'><i class='mdi mdi-arrow-right me-1'></i>View all {page_count} articles</a></li>"
        
        if not section.pages:
            page_list = "<em class='text-muted'>No articles yet</em>"
        
        card_html = f"""
        <div class="card h-100 border mb-3">
            <div class="card-body">
                <div class="d-flex align-items-center mb-3">
                    <div class="icon-box bg-primary bg-opacity-10 rounded p-3 me-3">
                        <i class="mdi mdi-{section.icon} text-primary" style="font-size: 1.5rem;"></i>
                    </div>
                    <div>
                        <h5 class="card-title mb-0">{section.title}</h5>
                        <small class="text-muted">{page_count} article{'s' if page_count != 1 else ''}</small>
                    </div>
                </div>
                <ul class="list-unstyled mb-0">{page_list}</ul>
            </div>
            <div class="card-footer bg-transparent">
                <a href="{url_for('help.section_index', section_id=section.id)}" class="btn btn-outline-primary btn-sm w-100">
                    View Section
                </a>
            </div>
        </div>
        """
        
        disp.add_display_item(
            DisplayerItemAlert(card_html, BSstyle.NONE),
            column=col, layout_id=layout_id
        )
        
        # Start a new row if needed
        if (idx + 1) % cols_per_row == 0 and idx + 1 < len(sections):
            remaining = len(sections) - (idx + 1)
            next_cols = min(remaining, cols_per_row)
            layout_id = disp.add_master_layout(DisplayerLayout(
                Layouts.HORIZONTAL,
                [col_width] * next_cols
            ))
    
    return render_template("base_content.j2", content=disp.display())


@bp.route('/<section_id>/')
def section_index(section_id: str):
    """Display section index with all pages in the section."""
    help_manager = _get_help_manager()
    if not help_manager:
        return _render_error_page("Help system not available", 503)
    
    section = help_manager.get_section(section_id)
    if not section or not section.enabled:
        return _render_error_page(f"Help section '{section_id}' not found", 404)
    
    disp = Displayer()
    disp.add_generic(TEXT_HELP, display=False)
    disp.set_title(section.title)
    disp.add_breadcrumb(TEXT_HELP, "help.index", [])
    disp.add_breadcrumb(section.title, "help.section_index", [section_id])
    
    # Section header
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    header_html = f"""
    <div class="d-flex align-items-center mb-3">
        <div class="icon-box bg-primary bg-opacity-10 rounded p-3 me-3">
            <i class="mdi mdi-{section.icon} text-primary" style="font-size: 1.5rem;"></i>
        </div>
        <div>
            <h4 class="mb-0">{section.title}</h4>
            <small class="text-muted">{len(section.pages)} article{'s' if len(section.pages) != 1 else ''}</small>
        </div>
    </div>
    """
    disp.add_display_item(DisplayerItemAlert(header_html, BSstyle.NONE))
    
    if not section.pages:
        disp.add_display_item(
            DisplayerItemAlert(
                f"<div class='text-center py-4'>"
                f"<i class='mdi mdi-file-document-outline text-muted' style='font-size: 3rem;'></i>"
                f"<h5 class='mt-3 text-muted'>{TEXT_NO_ARTICLES}</h5>"
                f"</div>",
                BSstyle.NONE
            )
        )
    else:
        # List of articles
        list_html = '<div class="list-group list-group-flush">'
        for page in section.pages:
            page_url = url_for('help.page', section_id=section.id, page_id=page.id)
            description = f"<p class='mb-0 text-muted small'>{page.description}</p>" if page.description else ""
            
            list_html += f"""
            <a href="{page_url}" class="list-group-item list-group-item-action d-flex align-items-start py-3">
                <i class="mdi mdi-file-document-outline text-primary me-3 mt-1" style="font-size: 1.25rem;"></i>
                <div class="flex-grow-1">
                    <h6 class="mb-1">{page.title}</h6>
                    {description}
                </div>
                <i class="mdi mdi-chevron-right text-muted"></i>
            </a>
            """
        list_html += '</div>'
        disp.add_display_item(DisplayerItemAlert(list_html, BSstyle.NONE))
    
    # Back button
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
    disp.add_breadcrumb(section.title, "help.section_index", [section_id])
    disp.add_breadcrumb(page_obj.title, "help.page", [section_id, page_id])
    
    # Add custom CSS for help content
    help_css = """
    <style>
        .help-content { line-height: 1.7; }
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
    </style>
    """
    
    toc = metadata.get('toc', '')
    
    # Layout: main content + optional TOC sidebar
    if toc:
        layout_id = disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, [9, 3]))
        
        # Main content
        content_html = f"{help_css}<div class='help-content'>{html_content}</div>"
        disp.add_display_item(DisplayerItemAlert(content_html, BSstyle.NONE), column=0, layout_id=layout_id)
        
        # TOC sidebar
        toc_html = f"""
        <div class="card" style="position: sticky; top: 1rem;">
            <div class="card-header">
                <h6 class="mb-0"><i class="mdi mdi-format-list-bulleted me-1"></i>{TEXT_ON_THIS_PAGE}</h6>
            </div>
            <div class="card-body" style="font-size: 0.875rem;">
                <div class="toc">{toc}</div>
            </div>
        </div>
        <style>
            .toc ul {{ list-style: none; padding-left: 1rem; }}
            .toc > ul {{ padding-left: 0; }}
            .toc a {{ color: var(--bs-secondary); text-decoration: none; }}
            .toc a:hover {{ color: var(--bs-primary); }}
        </style>
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
        prev_url = url_for('help.page', section_id=section.id, page_id=prev_page.id)
        prev_html = f"<a href='{prev_url}' class='btn btn-outline-primary'><i class='mdi mdi-arrow-left me-1'></i>{prev_page.title}</a>"
    else:
        prev_html = ""
    disp.add_display_item(DisplayerItemAlert(prev_html, BSstyle.NONE), column=0, layout_id=nav_layout_id)
    
    # Next button
    if next_page:
        next_url = url_for('help.page', section_id=section.id, page_id=next_page.id)
        next_html = f"<div class='text-end'><a href='{next_url}' class='btn btn-outline-primary'>{next_page.title}<i class='mdi mdi-arrow-right ms-1'></i></a></div>"
    else:
        next_html = ""
    disp.add_display_item(DisplayerItemAlert(next_html, BSstyle.NONE), column=1, layout_id=nav_layout_id)
    
    # Back to section button
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_back_section",
            text=f"{TEXT_BACK_TO_SECTION}: {section.title}",
            icon="arrow-left",
            link=url_for('help.section_index', section_id=section.id),
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
        section_states = {}
        for section in help_manager.get_all_sections():
            enabled = f"section_{section.id}" in request.form
            section_states[section.id] = enabled
        
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
    main_layout_id = disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, [8, 4]))
    
    # Left column: Configuration form
    if sections:
        # Info text
        info_html = f"<p class='text-muted mb-3'>{TEXT_ENABLE_DISABLE_INFO}</p>"
        disp.add_display_item(DisplayerItemAlert(info_html, BSstyle.NONE), column=0, layout_id=main_layout_id)
        
        # Build form with table
        table_html = """
        <form method="POST" action="">
        <div class="table-responsive">
        <table class="table table-hover">
            <thead>
                <tr>
                    <th style="width: 50px;">Enabled</th>
                    <th>Section</th>
                    <th>Source</th>
                    <th>Articles</th>
                    <th>Feature Requirement</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for section in sections:
            checked = "checked" if section.enabled else ""
            
            # Source badge
            if section.source == 'website':
                source_badge = '<span class="badge bg-info">Website</span>'
            elif section.source == 'framework':
                source_badge = '<span class="badge bg-secondary">Framework</span>'
            else:
                source_badge = f'<span class="badge bg-success">Plugin: {section.source}</span>'
            
            # Feature requirement
            feature_req = f"<code>{section.requires_feature}</code>" if section.requires_feature else '<span class="text-muted">—</span>'
            
            table_html += f"""
                <tr>
                    <td class="text-center">
                        <div class="form-check">
                            <input type="checkbox" class="form-check-input" name="section_{section.id}" id="section_{section.id}" {checked}>
                        </div>
                    </td>
                    <td>
                        <label for="section_{section.id}" class="mb-0 d-flex align-items-center">
                            <i class="mdi mdi-{section.icon} text-primary me-2"></i>
                            <strong>{section.title}</strong>
                        </label>
                        <small class="text-muted">{section.id}</small>
                    </td>
                    <td>{source_badge}</td>
                    <td><span class="badge bg-light text-dark">{len(section.pages)}</span></td>
                    <td>{feature_req}</td>
                </tr>
            """
        
        table_html += """
            </tbody>
        </table>
        </div>
        <div class="mt-3">
            <button type="submit" class="btn btn-primary">
                <i class="mdi mdi-content-save me-1"></i>Save Configuration
            </button>
            <a href="/help/" class="btn btn-outline-secondary ms-2">
                <i class="mdi mdi-eye me-1"></i>View Help Center
            </a>
        </div>
        </form>
        """
        
        disp.add_display_item(DisplayerItemAlert(table_html, BSstyle.NONE), column=0, layout_id=main_layout_id)
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
