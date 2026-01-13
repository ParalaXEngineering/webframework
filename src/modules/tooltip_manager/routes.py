"""Admin UI for tooltip management"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from src.modules import utilities
from src.modules.displayer import (
    Displayer, DisplayerLayout, Layouts, BSstyle, TableMode,
    DisplayerItemText, DisplayerItemButton, DisplayerItemAlert,
    DisplayerItemCard, DisplayerItemBadge, DisplayerItemActionButtons,
    DisplayerItemInputSelect, DisplayerItemInputMultiSelect, DisplayerItemInputText, DisplayerItemInputString
)
from src.modules.app_context import app_context
from src.modules.auth import require_permission
from src.modules.auth.permission_registry import permission_registry
from src.modules.log.logger_factory import get_logger

logger = get_logger(__name__)

# Permission constants
PERMISSION_MODULE = "TooltipManager"
PERMISSION_VIEW = "view"
PERMISSION_EDIT = "edit"
PERMISSION_DELETE = "delete"
PERMISSION_CREATE = "create"

# Register module permissions
permission_registry.register_module(PERMISSION_MODULE, [PERMISSION_CREATE, PERMISSION_EDIT, PERMISSION_DELETE])

bp = Blueprint('framework_tooltips', __name__, url_prefix='/admin/tooltips')


def get_tooltip_manager():
    """Helper to safely get tooltip manager"""
    return getattr(app_context, 'tooltip_manager', None)


@bp.route('/')
@require_permission(PERMISSION_MODULE, PERMISSION_VIEW)
def index():
    """List all tooltips and contexts in one page with DataTables"""
    tm = get_tooltip_manager()
    
    if not tm:
        flash("Tooltip manager is not enabled", "error")
        return redirect(url_for('tracker_admin.index'))
    
    # Check user permissions
    current_user = session.get('user', 'GUEST')
    can_create = app_context.auth_manager.has_permission(current_user, PERMISSION_MODULE, PERMISSION_CREATE) if app_context.auth_manager else True
    can_edit = app_context.auth_manager.has_permission(current_user, PERMISSION_MODULE, PERMISSION_EDIT) if app_context.auth_manager else True
    can_delete = app_context.auth_manager.has_permission(current_user, PERMISSION_MODULE, PERMISSION_DELETE) if app_context.auth_manager else True
    
    # Build displayer
    disp = Displayer()
    disp.add_generic("Tooltip Management", display=False)
    disp.set_title("Tooltip Management")
    disp.add_breadcrumb("Tooltip Management", "framework_tooltips.index", [])
    
    # Enable tooltips on this page (Global context)
    disp.set_tooltip_contexts(['Global'])
    
    # === TOOLTIPS SECTION ===
    tooltips_layout = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12], subtitle="Tooltips"))
    
    # Create Tooltip button
    if can_create:
        disp.add_display_item(
            DisplayerItemButton(
                "btn_create_tooltip",
                "Create New Tooltip",
                color=BSstyle.SUCCESS,
                icon="plus",
                link=url_for('framework_tooltips.create_tooltip')
            ),
            column=0, layout_id=tooltips_layout
        )
    
    # Get all tooltips
    all_tooltips, _ = tm.list_tooltips(limit=1000, offset=0)
    
    if all_tooltips:
        table_layout_id = disp.add_slave_layout(
            DisplayerLayout(
                Layouts.TABLE,
                ["Keyword", "Preview", "Type", "Contexts", "Actions"],
                datatable_config={
                    "table_id": "tooltips_table",
                    "mode": TableMode.INTERACTIVE,
                    "page_length": 25,
                    "searchable": True,
                    "ordering": [[0, "asc"]],
                    "columnDefs": [
                        {"orderable": False, "targets": [4]},
                        {"className": "text-center", "targets": [2, 4]}
                    ]
                }
            ),
            column=0,
            layout_id=tooltips_layout
        )
        
        for idx, tooltip in enumerate(all_tooltips):
            # Keyword
            disp.add_display_item(
                DisplayerItemText(tooltip['keyword']),
                column=0, line=idx, layout_id=table_layout_id
            )
            
            # Preview (truncate content)
            preview = tooltip['content'][:50] + '...' if len(tooltip['content']) > 50 else tooltip['content']
            disp.add_display_item(
                DisplayerItemText(preview),
                column=1, line=idx, layout_id=table_layout_id
            )
            
            # Type badge - always HTML
            disp.add_display_item(
                DisplayerItemBadge('html', BSstyle.INFO),
                column=2, line=idx, layout_id=table_layout_id
            )
            
            # Contexts
            contexts_str = ', '.join(tooltip.get('contexts', []))
            disp.add_display_item(
                DisplayerItemText(contexts_str),
                column=3, line=idx, layout_id=table_layout_id
            )
            
            # Actions
            actions = []
            if can_edit:
                actions.append({
                    "type": "custom",
                    "url": url_for('framework_tooltips.edit_tooltip', id=tooltip['id']),
                    "icon": "mdi mdi-pencil",
                    "style": "warning",
                    "tooltip": "Edit Tooltip"
                })
            if can_delete:
                actions.append({
                    "type": "custom",
                    "url": url_for('framework_tooltips.delete_tooltip', id=tooltip['id']),
                    "icon": "mdi mdi-delete",
                    "style": "danger",
                    "tooltip": "Delete Tooltip"
                })
            
            disp.add_display_item(
                DisplayerItemActionButtons(
                    id=f"tooltip_actions_{idx}",
                    actions=actions,
                    size="sm"
                ),
                column=4, line=idx, layout_id=table_layout_id
            )
    else:
        disp.add_display_item(
            DisplayerItemAlert("No tooltips found. Create one to get started.", BSstyle.INFO),
            column=0, layout_id=tooltips_layout
        )
    
    # === CONTEXTS SECTION ===
    contexts_layout = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12], subtitle="Contexts"))
    
    # Create Context button
    if can_create:
        disp.add_display_item(
            DisplayerItemButton(
                "btn_create_context",
                "Create New Context",
                color=BSstyle.SUCCESS,
                icon="plus",
                link=url_for('framework_tooltips.create_context')
            ),
            column=0, layout_id=contexts_layout
        )
    
    # Get all contexts
    contexts_list = tm.list_contexts()
    
    if contexts_list:
        ctx_table_layout_id = disp.add_slave_layout(
            DisplayerLayout(
                Layouts.TABLE,
                ["Name", "Description", "Strategy", "Tooltips", "Actions"],
                datatable_config={
                    "table_id": "contexts_table",
                    "mode": TableMode.INTERACTIVE,
                    "page_length": 25,
                    "searchable": True,
                    "ordering": [[0, "asc"]],
                    "columnDefs": [
                        {"orderable": False, "targets": [4]},
                        {"className": "text-center", "targets": [2, 3, 4]}
                    ]
                }
            ),
            column=0,
            layout_id=contexts_layout
        )
        
        for idx, ctx in enumerate(contexts_list):
            # Name - add badge if Global
            name_text = ctx['name']
            if ctx['name'] == 'Global':
                name_html = f"{name_text} <span class='badge bg-primary'>System</span>"
                disp.add_display_item(
                    DisplayerItemAlert(name_html, BSstyle.NONE),
                    column=0, line=idx, layout_id=ctx_table_layout_id
                )
            else:
                disp.add_display_item(
                    DisplayerItemText(name_text),
                    column=0, line=idx, layout_id=ctx_table_layout_id
                )
            
            # Description
            disp.add_display_item(
                DisplayerItemText(ctx.get('description', '')),
                column=1, line=idx, layout_id=ctx_table_layout_id
            )
            
            # Strategy
            disp.add_display_item(
                DisplayerItemBadge(ctx['matching_strategy'], BSstyle.INFO),
                column=2, line=idx, layout_id=ctx_table_layout_id
            )
            
            # Tooltip count
            disp.add_display_item(
                DisplayerItemText(str(ctx.get('tooltip_count', 0))),
                column=3, line=idx, layout_id=ctx_table_layout_id
            )
            
            # Actions - allow edit, but hide delete for Global context
            actions = []
            if can_edit:
                actions.append({
                    "type": "custom",
                    "url": url_for('framework_tooltips.edit_context', id=ctx['id']),
                    "icon": "mdi mdi-pencil",
                    "style": "warning",
                    "tooltip": "Edit Context"
                })
            if can_delete and ctx['name'] != 'Global':
                actions.append({
                    "type": "custom",
                    "url": url_for('framework_tooltips.delete_context', id=ctx['id']),
                    "icon": "mdi mdi-delete",
                    "style": "danger",
                    "tooltip": "Delete Context"
                })
            
            disp.add_display_item(
                DisplayerItemActionButtons(
                    id=f"context_actions_{idx}",
                    actions=actions,
                    size="sm"
                ),
                column=4, line=idx, layout_id=ctx_table_layout_id
            )
    else:
        disp.add_display_item(
            DisplayerItemAlert("No contexts found. Create one to get started.", BSstyle.INFO),
            column=0, layout_id=contexts_layout
        )
    
    return render_template('base_content.j2', content=disp.display())


@bp.route('/tooltip/create', methods=['GET', 'POST'])
@require_permission(PERMISSION_MODULE, PERMISSION_CREATE)
def create_tooltip():
    """Create new tooltip"""
    tm = get_tooltip_manager()
    if not tm:
        flash("Tooltip manager is not enabled", "error")
        return redirect(url_for('tracker_admin.index'))
    
    if request.method == 'POST':
        try:
            logger.debug(f"Raw form data: {dict(request.form)}")
            data_in = utilities.util_post_to_json(dict(request.form))
            logger.debug(f"After util_post_to_json: {data_in}")
            form_data = data_in.get("Create Tooltip", {})
            logger.debug(f"Form data: {form_data}")
            
            keyword = form_data.get("keyword", "").strip()
            content = form_data.get("content", "").strip()
            
            # Handle contexts from multi-select widget (stored as .list0, .list1, etc. in raw form)
            context_selections = []
            for key, value in request.form.items():
                if key.startswith('Create Tooltip.contexts.list') and value.strip():
                    context_selections.append(value.strip())
            
            logger.debug(f"Context selections raw: {context_selections} (type: {type(context_selections)})")
            # Extract context names from formatted strings ("Name - Description" -> "Name")
            context_names = [sel.split(' - ')[0] for sel in context_selections]
            logger.debug(f"Context names extracted: {context_names}")
            
            if not keyword or not content:
                flash("Keyword and content are required", "error")
                return redirect(request.url)
            
            if not context_names:
                flash("At least one context is required", "error")
                return redirect(request.url)
            
            # Register tooltip
            tm.register_tooltip(keyword, content, context_names)
            flash(f"Tooltip '{keyword}' created successfully", "success")
            return redirect(url_for('framework_tooltips.index'))
            
        except Exception as e:
            flash(f"Error creating tooltip: {e}", "error")
            logger.error(f"Error creating tooltip: {e}", exc_info=True)
    
    # GET - show form
    contexts = tm.list_contexts()
    
    disp = Displayer()
    disp.add_generic('Create Tooltip', display=False)
    disp.set_title('Create Tooltip')
    disp.add_breadcrumb("Tooltip Management", "framework_tooltips.index", [])
    disp.add_breadcrumb("Create Tooltip", "framework_tooltips.create_tooltip", [])
    
    layout = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    
    # Keyword
    disp.add_display_item(
        DisplayerItemInputString(
            id="keyword",
            text="Keyword"
        ),
        column=0, layout_id=layout
    )
    
    # Content (WYSIWYG editor for HTML formatting)
    disp.add_display_item(
        DisplayerItemInputText(
            id="content",
            text="Content"
        ),
        column=0, layout_id=layout
    )
    
    # Contexts
    context_choices = [f"{ctx['name']} - {ctx.get('description', '')}" for ctx in contexts]
    
    disp.add_display_item(
        DisplayerItemInputMultiSelect(
            id="contexts",
            text="Contexts (select at least one)",
            choices=context_choices
        ),
        column=0, layout_id=layout
    )
    
    # Buttons
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_submit",
            text="Create Tooltip",
            color=BSstyle.SUCCESS,
            icon="check"
        ),
        column=0, layout_id=layout
    )
    
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_cancel",
            text="Cancel",
            color=BSstyle.SECONDARY,
            link=url_for('framework_tooltips.index')
        ),
        column=0, layout_id=layout
    )
    
    return render_template('base_content.j2', content=disp.display(),
                         form_action=url_for('framework_tooltips.create_tooltip'))


@bp.route('/tooltip/edit/<int:id>', methods=['GET', 'POST'])
@require_permission(PERMISSION_MODULE, PERMISSION_EDIT)
def edit_tooltip(id):
    """Edit tooltip"""
    tm = get_tooltip_manager()
    if not tm:
        flash("Tooltip manager is not enabled", "error")
        return redirect(url_for('tracker_admin.index'))
    
    tooltip = tm.get_tooltip(id)
    if not tooltip:
        flash("Tooltip not found", "error")
        return redirect(url_for('framework_tooltips.index'))
    
    if request.method == 'POST':
        try:
            logger.info(f"Raw form data: {dict(request.form)}")
            data_in = utilities.util_post_to_json(dict(request.form))
            logger.info(f"After util_post_to_json: {data_in}")
            form_data = data_in.get("Edit Tooltip", {})
            logger.info(f"Form data: {form_data}")
            
            keyword = form_data.get("keyword", "").strip()
            content = form_data.get("content", "").strip()
            
            # Handle contexts from multi-select widget (stored as .list0, .list1, etc. in raw form)
            context_selections = []
            for key, value in request.form.items():
                if key.startswith('Edit Tooltip.contexts.list') and value.strip():
                    context_selections.append(value.strip())
            
            logger.info(f"Context selections raw: {context_selections} (type: {type(context_selections)})")
            # Extract context names from formatted strings ("Name - Description" -> "Name")
            context_names = [sel.split(' - ')[0] for sel in context_selections]
            logger.info(f"Context names extracted: {context_names}")
            
            if not keyword or not content:
                flash("Keyword and content are required", "error")
                return redirect(request.url)
            
            if not context_names:
                flash("At least one context is required", "error")
                return redirect(request.url)
            
            # Update tooltip
            tm.update_tooltip(id, keyword=keyword, content=content)
            
            # Get context IDs from names
            all_contexts = tm.list_contexts()
            context_ids = [ctx['id'] for ctx in all_contexts if ctx['name'] in context_names]
            
            # Update contexts
            tm.assign_tooltip_to_contexts(id, context_ids)
            
            flash(f"Tooltip '{keyword}' updated successfully", "success")
            return redirect(url_for('framework_tooltips.index'))
            
        except Exception as e:
            flash(f"Error updating tooltip: {e}", "error")
            logger.error(f"Error updating tooltip: {e}", exc_info=True)
    
    # GET - show form with existing data
    all_contexts = tm.list_contexts()
    
    disp = Displayer()
    disp.add_generic('Edit Tooltip', display=False)
    disp.set_title(f'Edit Tooltip: {tooltip["keyword"]}')
    disp.add_breadcrumb("Tooltip Management", "framework_tooltips.index", [])
    disp.add_breadcrumb("Edit Tooltip", "framework_tooltips.edit_tooltip", [f"id={id}"])
    
    layout = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    
    # Keyword
    disp.add_display_item(
        DisplayerItemInputString(
            id="keyword",
            text="Keyword",
            value=tooltip['keyword']
        ),
        column=0, layout_id=layout
    )
    
    # Content (WYSIWYG editor for HTML formatting)
    disp.add_display_item(
        DisplayerItemInputText(
            id="content",
            text="Content",
            value=tooltip['content']
        ),
        column=0, layout_id=layout
    )
    
    # Contexts
    context_choices = [f"{ctx['name']} - {ctx.get('description', '')}" for ctx in all_contexts]
    # Pre-select current contexts
    tooltip_contexts = tooltip.get('contexts', [])
    selected_values = [f"{ctx['name']} - {ctx.get('description', '')}" for ctx in all_contexts if ctx['name'] in tooltip_contexts]
    
    disp.add_display_item(
        DisplayerItemInputMultiSelect(
            id="contexts",
            text="Contexts (select at least one)",
            choices=context_choices,
            value=selected_values
        ),
        column=0, layout_id=layout
    )
    
    # Buttons
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_submit",
            text="Update Tooltip",
            color=BSstyle.PRIMARY,
            icon="check"
        ),
        column=0, layout_id=layout
    )
    
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_cancel",
            text="Cancel",
            color=BSstyle.SECONDARY,
            link=url_for('framework_tooltips.index')
        ),
        column=0, layout_id=layout
    )
    
    return render_template('base_content.j2', content=disp.display(),
                         form_action=url_for('framework_tooltips.edit_tooltip', id=id))


@bp.route('/tooltip/delete/<int:id>', methods=['GET', 'POST'])
@require_permission(PERMISSION_MODULE, PERMISSION_DELETE)
def delete_tooltip(id):
    """Delete tooltip"""
    tm = get_tooltip_manager()
    if not tm:
        flash("Tooltip manager is not enabled", "error")
        return redirect(url_for('tracker_admin.index'))
    
    tooltip = tm.get_tooltip(id)
    if not tooltip:
        flash("Tooltip not found", "error")
        return redirect(url_for('framework_tooltips.index'))
    
    if request.method == 'POST':
        tm.delete_tooltip(id)
        flash(f"Tooltip '{tooltip['keyword']}' deleted successfully", "success")
        return redirect(url_for('framework_tooltips.index'))
    
    # GET - show confirmation
    disp = Displayer()
    disp.add_generic('Delete Tooltip', display=False)
    disp.set_title(f'Delete Tooltip: {tooltip["keyword"]}')
    disp.add_breadcrumb("Tooltip Management", "framework_tooltips.index", [])
    disp.add_breadcrumb("Delete Tooltip", "framework_tooltips.delete_tooltip", [f"id={id}"])
    
    layout = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    
    # Warning message
    contexts_str = ', '.join(tooltip.get('contexts', []))
    warning_html = f"""
    Are you sure you want to delete the tooltip '<strong>{tooltip['keyword']}</strong>'?<br>
    <strong>Contexts:</strong> {contexts_str}<br>
    <strong>Content Preview:</strong> {tooltip['content'][:100]}{'...' if len(tooltip['content']) > 100 else ''}<br><br>
    This action cannot be undone.
    """
    
    disp.add_display_item(
        DisplayerItemAlert(warning_html, BSstyle.ERROR, icon="alert", title="Confirm Deletion"),
        column=0, layout_id=layout
    )
    
    # Buttons
    button_layout = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [6, 6]))
    
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_submit",
            text="Yes, Delete",
            color=BSstyle.ERROR,
            icon="delete-forever"
        ),
        column=0, layout_id=button_layout
    )
    
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_cancel",
            text="Cancel",
            color=BSstyle.SECONDARY,
            icon="close-circle",
            link=url_for('framework_tooltips.index')
        ),
        column=1, layout_id=button_layout
    )
    
    return render_template('base_content.j2', content=disp.display(), 
                         form_action=url_for('framework_tooltips.delete_tooltip', id=id))


@bp.route('/context/create', methods=['GET', 'POST'])
@require_permission(PERMISSION_MODULE, PERMISSION_CREATE)
def create_context():
    """Create new context"""
    tm = get_tooltip_manager()
    if not tm:
        flash("Tooltip manager is not enabled", "error")
        return redirect(url_for('tracker_admin.index'))
    
    if request.method == 'POST':
        try:
            data_in = utilities.util_post_to_json(dict(request.form))
            form_data = data_in.get("Create Context", {})
            
            name = form_data.get("name", "").strip()
            description = form_data.get("description", "").strip()
            strategy = form_data.get("matching_strategy", "exact")
            
            if not name:
                flash("Context name is required", "error")
                return redirect(request.url)
            
            tm.create_context(name, description, strategy)
            flash(f"Context '{name}' created successfully", "success")
            return redirect(url_for('framework_tooltips.index'))
            
        except ValueError as e:
            flash(str(e), "error")
            return redirect(request.url)
        except Exception as e:
            flash(f"Error creating context: {e}", "error")
            logger.error(f"Error creating context: {e}", exc_info=True)
            return redirect(request.url)
    
    # GET - show form
    disp = Displayer()
    disp.add_generic('Create Context', display=False)
    disp.set_title('Create Context')
    disp.add_breadcrumb("Tooltip Management", "framework_tooltips.index", [])
    disp.add_breadcrumb("Create Context", "framework_tooltips.create_context", [])
    
    layout = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    
    # Name
    disp.add_display_item(
        DisplayerItemInputString(
            id="name",
            text="Name (alphanumeric and underscore only)"
        ),
        column=0, layout_id=layout
    )
    
    # Description
    disp.add_display_item(
        DisplayerItemInputString(
            id="description",
            text="Description"
        ),
        column=0, layout_id=layout
    )
    
    # Matching Strategy
    disp.add_display_item(
        DisplayerItemInputSelect(
            id="matching_strategy",
            text="Matching Strategy",
            choices=["exact", "word_boundary", "regex"],
            value="exact"
        ),
        column=0, layout_id=layout
    )
    
    # Buttons
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_submit",
            text="Create Context",
            color=BSstyle.SUCCESS,
            icon="check"
        ),
        column=0, layout_id=layout
    )
    
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_cancel",
            text="Cancel",
            color=BSstyle.SECONDARY,
            link=url_for('framework_tooltips.index')
        ),
        column=0, layout_id=layout
    )
    
    return render_template('base_content.j2', content=disp.display(),
                         form_action=url_for('framework_tooltips.create_context'))


@bp.route('/context/edit/<int:id>', methods=['GET', 'POST'])
@require_permission(PERMISSION_MODULE, PERMISSION_EDIT)
def edit_context(id):
    """Edit context"""
    tm = get_tooltip_manager()
    if not tm:
        flash("Tooltip manager is not enabled", "error")
        return redirect(url_for('tracker_admin.index'))
    
    # Get context
    all_contexts = tm.list_contexts()
    ctx = next((c for c in all_contexts if c['id'] == id), None)
    if not ctx:
        flash("Context not found", "error")
        return redirect(url_for('framework_tooltips.index'))
    
    # Prevent editing Global context
    if ctx['name'] == 'Global':
        flash("Cannot edit Global context - it is a system context", "error")
        return redirect(url_for('framework_tooltips.index'))
    
    if request.method == 'POST':
        try:
            data_in = utilities.util_post_to_json(dict(request.form))
            form_data = data_in.get("Edit Context", {})
            
            description = form_data.get("description", "").strip()
            strategy = form_data.get("matching_strategy", "exact")
            
            tm.update_context(id, description=description, matching_strategy=strategy)
            flash(f"Context '{ctx['name']}' updated successfully", "success")
            return redirect(url_for('framework_tooltips.index'))
            
        except Exception as e:
            flash(f"Error updating context: {e}", "error")
            logger.error(f"Error updating context: {e}", exc_info=True)
    
    # GET - show form
    disp = Displayer()
    disp.add_generic('Edit Context', display=False)
    disp.set_title(f'Edit Context: {ctx["name"]}')
    disp.add_breadcrumb("Tooltip Management", "framework_tooltips.index", [])
    disp.add_breadcrumb("Edit Context", "framework_tooltips.edit_context", [f"id={id}"])
    
    layout = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    
    # Name (read-only) - show as alert
    disp.add_display_item(
        DisplayerItemAlert(
            f"<strong>Name (cannot be changed):</strong> {ctx['name']}",
            BSstyle.INFO
        ),
        column=0, layout_id=layout
    )
    
    # Description
    disp.add_display_item(
        DisplayerItemInputString(
            id="description",
            text="Description",
            value=ctx.get('description', '')
        ),
        column=0, layout_id=layout
    )
    
    # Matching Strategy
    disp.add_display_item(
        DisplayerItemInputSelect(
            id="matching_strategy",
            text="Matching Strategy",
            choices=["exact", "word_boundary", "regex"],
            value=ctx['matching_strategy']
        ),
        column=0, layout_id=layout
    )
    
    # Buttons
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_submit",
            text="Update Context",
            color=BSstyle.PRIMARY,
            icon="check"
        ),
        column=0, layout_id=layout
    )
    
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_cancel",
            text="Cancel",
            color=BSstyle.SECONDARY,
            link=url_for('framework_tooltips.index')
        ),
        column=0, layout_id=layout
    )
    
    return render_template('base_content.j2', content=disp.display(),
                         form_action=url_for('framework_tooltips.edit_context', id=id))


@bp.route('/context/delete/<int:id>', methods=['GET', 'POST'])
@require_permission(PERMISSION_MODULE, PERMISSION_DELETE)
def delete_context(id):
    """Delete context"""
    tm = get_tooltip_manager()
    if not tm:
        flash("Tooltip manager is not enabled", "error")
        return redirect(url_for('tracker_admin.index'))
    
    # Get context
    all_contexts = tm.list_contexts()
    ctx = next((c for c in all_contexts if c['id'] == id), None)
    if not ctx:
        flash("Context not found", "error")
        return redirect(url_for('framework_tooltips.index'))
    
    # Prevent deleting Global context
    if ctx['name'] == 'Global':
        flash("Cannot delete Global context - it is a system context", "error")
        return redirect(url_for('framework_tooltips.index'))
    
    if request.method == 'POST':
        try:
            tm.delete_context(id)
            flash(f"Context '{ctx['name']}' deleted successfully", "success")
            return redirect(url_for('framework_tooltips.index'))
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for('framework_tooltips.index'))
        except Exception as e:
            flash(f"Error deleting context: {e}", "error")
            logger.error(f"Error deleting context: {e}", exc_info=True)
            return redirect(url_for('framework_tooltips.index'))
    
    # GET - show confirmation
    disp = Displayer()
    disp.add_generic('Delete Context', display=False)
    disp.set_title(f'Delete Context: {ctx["name"]}')
    disp.add_breadcrumb("Tooltip Management", "framework_tooltips.index", [])
    disp.add_breadcrumb("Delete Context", "framework_tooltips.delete_context", [f"id={id}"])
    
    layout = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    
    # Warning message
    warning_msg = f"Are you sure you want to delete the context '<strong>{ctx['name']}</strong>'?<br>"
    warning_msg += f"<strong>Description:</strong> {ctx.get('description', 'N/A')}<br>"
    warning_msg += f"<strong>Matching Strategy:</strong> {ctx['matching_strategy']}<br>"
    warning_msg += f"<strong>Associated Tooltips:</strong> {ctx.get('tooltip_count', 0)}<br><br>"
    
    if ctx.get('tooltip_count', 0) > 0:
        warning_msg += f"This context has {ctx['tooltip_count']} tooltip(s) associated with it. The tooltips will not be deleted, but they will no longer be associated with this context.<br><br>"
    
    warning_msg += "This action cannot be undone."
    
    disp.add_display_item(
        DisplayerItemAlert(warning_msg, BSstyle.ERROR, icon="alert", title="Confirm Deletion"),
        column=0, layout_id=layout
    )
    
    # Buttons
    button_layout = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [6, 6]))
    
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_submit",
            text="Yes, Delete",
            color=BSstyle.ERROR,
            icon="delete-forever"
        ),
        column=0, layout_id=button_layout
    )
    
    disp.add_display_item(
        DisplayerItemButton(
            id="btn_cancel",
            text="Cancel",
            color=BSstyle.SECONDARY,
            icon="close-circle",
            link=url_for('framework_tooltips.index')
        ),
        column=1, layout_id=button_layout
    )
    
    return render_template('base_content.j2', content=disp.display(), 
                         form_action=url_for('framework_tooltips.delete_context', id=id))

