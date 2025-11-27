"""
Authorization Showcase Demo

Interactive demo of the framework's authorization system.
"""

from flask import Blueprint, render_template, session, url_for
from src.modules import displayer
from src.modules.auth import require_permission, require_admin, auth_manager
from src.modules.auth.permission_registry import permission_registry
from src.modules.log.logger_factory import get_logger

logger = get_logger(__name__)

demo_auth_bp = Blueprint('demo_auth', __name__, url_prefix='/demo/authorization')

# Register the Demo_Auth module with actions
permission_registry.register_module("Demo_Auth", ["view", "edit", "delete", "custom_action"])


@demo_auth_bp.route('/')
def index():
    """Main authorization showcase page."""
    current_user = session.get('user', 'GUEST')
    
    disp = displayer.Displayer()
    disp.add_generic("Authorization Showcase")
    disp.set_title("Authorization System Demo")
    
    from src.modules.utilities import get_home_endpoint
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("Authorization Showcase", "demo_auth.index", [])
    
    # Section 1: Overview
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Permission System Overview"
    ))
    
    disp.add_display_item(displayer.DisplayerItemText(
        "The framework uses Module + Action permissions. Decorators check if user's groups have access."
    ), 0)
    
    # Current user info
    if auth_manager:
        user_obj = auth_manager.get_user(current_user)
        if user_obj:
            groups_str = ', '.join(user_obj.groups) if user_obj.groups else 'None'
            demo_permissions = auth_manager.get_user_permissions(current_user, "Demo_Auth")
            perms_str = ', '.join(demo_permissions) if demo_permissions else 'None'
            
            disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                ["Property", "Value"],
                subtitle="Your Session"
            ))
            disp.add_display_item(displayer.DisplayerItemText("Username"), 0)
            disp.add_display_item(displayer.DisplayerItemText(current_user), 1)
            disp.add_display_item(displayer.DisplayerItemText("Groups"), 0, line=1)
            disp.add_display_item(displayer.DisplayerItemText(groups_str), 1, line=1)
            disp.add_display_item(displayer.DisplayerItemText("Is Admin"), 0, line=2)
            disp.add_display_item(displayer.DisplayerItemText("Yes" if 'admin' in user_obj.groups else "No"), 1, line=2)
            disp.add_display_item(displayer.DisplayerItemText("Demo_Auth Permissions"), 0, line=3)
            disp.add_display_item(displayer.DisplayerItemText(perms_str), 1, line=3)
    else:
        disp.add_display_item(displayer.DisplayerItemAlert(
            "Auth system is disabled - all permission checks will pass",
            displayer.BSstyle.WARNING
        ), 0)
    
    # Section 2: Decorator Examples
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Decorator Usage"
    ))
    
    code_examples = '''# Basic permission check
@require_permission("Demo_Auth", "view")
def test_view():
    return "View access granted"

# Admin only
@require_admin()
def test_admin():
    return "Admin access granted"

# Custom action
@require_permission("Demo_Auth", "delete")
def test_delete():
    return "Delete access granted"'''
    
    disp.add_display_item(displayer.DisplayerItemCode("code_decorators", code_examples, language="python"), 0)
    
    # Section 3: Interactive Tests
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Interactive Permission Tests"
    ))
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [4, 4, 4]))
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_public", "Public (No Auth)", icon="lock-open-variant",
        link=url_for('demo_auth.test_public'),
        color=displayer.BSstyle.SUCCESS
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_view", "View Permission", icon="eye",
        link=url_for('demo_auth.test_view'),
        color=displayer.BSstyle.PRIMARY
    ), 1)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_edit", "Edit Permission", icon="pencil",
        link=url_for('demo_auth.test_edit'),
        color=displayer.BSstyle.WARNING
    ), 2)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [4, 4, 4]))
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_delete", "Denied Permission", icon="cancel",
        link=url_for('demo_auth.test_delete'),
        color=displayer.BSstyle.ERROR
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_custom", "Allowed Permission", icon="check-circle",
        link=url_for('demo_auth.test_custom'),
        color=displayer.BSstyle.SUCCESS
    ), 1)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_admin", "Admin Only", icon="shield-crown",
        link=url_for('demo_auth.test_admin'),
        color=displayer.BSstyle.ERROR
    ), 2)
    
    # Section 4: Inline Checks
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Inline Permission Checks"
    ))
    
    inline_code = '''from src.modules.auth import auth_manager

current_user = session.get("user")

# Runtime check
if auth_manager and not auth_manager.has_permission(current_user, "Module", "action"):
    return "No permission"'''
    
    disp.add_display_item(displayer.DisplayerItemCode("code_inline", inline_code, language="python"), 0)
    
    # Live check results
    can_edit = auth_manager.has_permission(current_user, "Demo_Auth", "edit") if auth_manager else True
    can_delete = auth_manager.has_permission(current_user, "Demo_Auth", "delete") if auth_manager else True
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        ["Check", "Result"],
        subtitle="Live Results"
    ))
    disp.add_display_item(displayer.DisplayerItemText('has_permission("Demo_Auth", "edit")'), 0)
    disp.add_display_item(displayer.DisplayerItemText("True" if can_edit else "False"), 1)
    disp.add_display_item(displayer.DisplayerItemText('has_permission("Demo_Auth", "delete")'), 0, line=1)
    disp.add_display_item(displayer.DisplayerItemText("True" if can_delete else "False"), 1, line=1)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_inline_demo", "Test Inline Check Page", icon="code-braces",
        link=url_for('demo_auth.inline_check_demo'),
        color=displayer.BSstyle.INFO
    ), 0)
    
    # Section 5: Module-Level
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Module-Level Authorization"
    ))
    
    module_code = '''from src.modules.action import Action

class ProtectedAction(Action):
    m_default_name = "Secret Feature"
    m_required_permission = "Demo_Auth"
    m_required_action = "view"
    
    def start(self):
        return "Secret data"

disp.add_module(ProtectedAction)  # Auto-checks permission'''
    
    disp.add_display_item(displayer.DisplayerItemCode("code_module", module_code, language="python"), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_module_demo", "Test Module Authorization", icon="package-variant",
        link=url_for('demo_auth.module_demo'),
        color=displayer.BSstyle.PRIMARY
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


# Test Pages
@demo_auth_bp.route('/test/public')
def test_public():
    """No authentication required."""
    disp = displayer.Displayer()
    disp.add_generic("Public Access Test")
    
    from src.modules.utilities import get_home_endpoint
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("Authorization Showcase", "demo_auth.index", [])
    disp.add_breadcrumb("Public Test", "demo_auth.test_public", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "Access Granted - This page has NO decorators",
        displayer.BSstyle.SUCCESS
    ), 0)
    
    code = '''@demo_auth_bp.route("/test/public")
def test_public():
    # No @require_permission decorator
    return "Public content"'''
    disp.add_display_item(displayer.DisplayerItemCode("code_public", code, language="python"), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_back", "Back", icon="arrow-left",
        link=url_for('demo_auth.index'),
        color=displayer.BSstyle.SECONDARY
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_auth_bp.route('/test/view')
@require_permission("Demo_Auth", "view")
def test_view():
    """Requires 'view' permission."""
    current_user = session.get('user', 'GUEST')
    
    disp = displayer.Displayer()
    disp.add_generic("View Permission Test")
    
    from src.modules.utilities import get_home_endpoint
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("Authorization Showcase", "demo_auth.index", [])
    disp.add_breadcrumb("View Test", "demo_auth.test_view", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemAlert(
        f'View Access Granted for {current_user}',
        displayer.BSstyle.SUCCESS
    ), 0)
    
    code = '''@require_permission("Demo_Auth", "view")
def test_view():
    return "View granted"'''
    disp.add_display_item(displayer.DisplayerItemCode("code_view", code, language="python"), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_back", "Back", icon="arrow-left",
        link=url_for('demo_auth.index'),
        color=displayer.BSstyle.SECONDARY
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_auth_bp.route('/test/edit')
@require_permission("Demo_Auth", "edit")
def test_edit():
    """Requires 'edit' permission."""
    current_user = session.get('user', 'GUEST')
    
    disp = displayer.Displayer()
    disp.add_generic("Edit Permission Test")
    
    from src.modules.utilities import get_home_endpoint
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("Authorization Showcase", "demo_auth.index", [])
    disp.add_breadcrumb("Edit Test", "demo_auth.test_edit", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemAlert(
        f'Edit Access Granted for {current_user}',
        displayer.BSstyle.SUCCESS
    ), 0)
    
    code = '''@require_permission("Demo_Auth", "edit")
def test_edit():
    return "Edit granted"'''
    disp.add_display_item(displayer.DisplayerItemCode("code_edit", code, language="python"), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_back", "Back", icon="arrow-left",
        link=url_for('demo_auth.index'),
        color=displayer.BSstyle.SECONDARY
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_auth_bp.route('/test/delete')
@require_permission("Demo_Auth", "delete")
def test_delete():
    """Requires 'delete' permission."""
    current_user = session.get('user', 'GUEST')
    
    disp = displayer.Displayer()
    disp.add_generic("Denied Permission Test")
    
    from src.modules.utilities import get_home_endpoint
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("Authorization Showcase", "demo_auth.index", [])
    disp.add_breadcrumb("Denied Test", "demo_auth.test_delete", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemAlert(
        f'Access Granted for {current_user} - You have the "delete" permission',
        displayer.BSstyle.SUCCESS
    ), 0)
    
    code = '''@require_permission("Demo_Auth", "delete")
def test_delete():
    return "Delete granted"'''
    disp.add_display_item(displayer.DisplayerItemCode("code_delete", code, language="python"), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_back", "Back", icon="arrow-left",
        link=url_for('demo_auth.index'),
        color=displayer.BSstyle.SECONDARY
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_auth_bp.route('/test/custom')
@require_permission("Demo_Auth", "custom_action")
def test_custom():
    """Requires 'custom_action' permission."""
    current_user = session.get('user', 'GUEST')
    
    disp = displayer.Displayer()
    disp.add_generic("Allowed Permission Test")
    
    from src.modules.utilities import get_home_endpoint
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("Authorization Showcase", "demo_auth.index", [])
    disp.add_breadcrumb("Allowed Test", "demo_auth.test_custom", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemAlert(
        f'Access Granted for {current_user} - You have the "custom_action" permission',
        displayer.BSstyle.SUCCESS
    ), 0)
    
    code = '''@require_permission("Demo_Auth", "custom_action")
def test_custom():
    return "Custom action granted"

# Register custom actions:
permission_registry.register_module("Demo_Auth", ["custom_action"])'''
    disp.add_display_item(displayer.DisplayerItemCode("code_custom", code, language="python"), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_back", "Back", icon="arrow-left",
        link=url_for('demo_auth.index'),
        color=displayer.BSstyle.SECONDARY
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_auth_bp.route('/test/admin')
@require_admin()
def test_admin():
    """Requires admin group."""
    current_user = session.get('user', 'GUEST')
    
    disp = displayer.Displayer()
    disp.add_generic("Admin Test")
    
    from src.modules.utilities import get_home_endpoint
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("Authorization Showcase", "demo_auth.index", [])
    disp.add_breadcrumb("Admin Test", "demo_auth.test_admin", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemAlert(
        f'Admin Access Granted for {current_user}',
        displayer.BSstyle.SUCCESS
    ), 0)
    
    code = '''from src.modules.auth import require_admin

@require_admin()
def test_admin():
    return "Admin granted"'''
    disp.add_display_item(displayer.DisplayerItemCode("code_admin", code, language="python"), 0)
    
    disp.add_display_item(displayer.DisplayerItemText(
        "The 'admin' group has ALL permissions automatically."
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_back", "Back", icon="arrow-left",
        link=url_for('demo_auth.index'),
        color=displayer.BSstyle.SECONDARY
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_auth_bp.route('/inline-check-demo')
def inline_check_demo():
    """Demonstrates inline permission checking."""
    current_user = session.get('user', 'GUEST')
    
    disp = displayer.Displayer()
    disp.add_generic("Inline Check Demo")
    
    from src.modules.utilities import get_home_endpoint
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("Authorization Showcase", "demo_auth.index", [])
    disp.add_breadcrumb("Inline Check", "demo_auth.inline_check_demo", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    
    code = '''from src.modules.auth import auth_manager

current_user = session.get("user")

has_edit = auth_manager.has_permission(current_user, "Demo_Auth", "edit")
has_delete = auth_manager.has_permission(current_user, "Demo_Auth", "delete")

# Customize response based on permissions'''
    disp.add_display_item(displayer.DisplayerItemCode("code_inline_demo", code, language="python"), 0)
    
    # Perform checks
    has_view = auth_manager.has_permission(current_user, "Demo_Auth", "view") if auth_manager else True
    has_edit = auth_manager.has_permission(current_user, "Demo_Auth", "edit") if auth_manager else True
    has_delete = auth_manager.has_permission(current_user, "Demo_Auth", "delete") if auth_manager else True
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        ["Permission", "Result"]
    ))
    disp.add_display_item(displayer.DisplayerItemText("View"), 0)
    disp.add_display_item(displayer.DisplayerItemText("True" if has_view else "False"), 1)
    disp.add_display_item(displayer.DisplayerItemText("Edit"), 0, line=1)
    disp.add_display_item(displayer.DisplayerItemText("True" if has_edit else "False"), 1, line=1)
    disp.add_display_item(displayer.DisplayerItemText("Delete"), 0, line=2)
    disp.add_display_item(displayer.DisplayerItemText("True" if has_delete else "False"), 1, line=2)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    
    if has_view and has_edit and has_delete:
        disp.add_display_item(displayer.DisplayerItemAlert(
            "Full Access - All permissions granted",
            displayer.BSstyle.SUCCESS
        ), 0)
    elif has_view and has_edit:
        disp.add_display_item(displayer.DisplayerItemAlert(
            "Editor - Can view and edit only",
            displayer.BSstyle.WARNING
        ), 0)
    elif has_view:
        disp.add_display_item(displayer.DisplayerItemAlert(
            "Viewer - Read-only access",
            displayer.BSstyle.INFO
        ), 0)
    else:
        disp.add_display_item(displayer.DisplayerItemAlert(
            "Restricted - No view permission",
            displayer.BSstyle.ERROR
        ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_back", "Back", icon="arrow-left",
        link=url_for('demo_auth.index'),
        color=displayer.BSstyle.SECONDARY
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_auth_bp.route('/module-demo')
def module_demo():
    """Demonstrates module-level authorization."""
    from src.modules.action import Action
    
    class ProtectedAction(Action):
        """Action requiring Demo_Auth view permission."""
        m_default_name = "Protected Module"
        m_required_permission = "Demo_Auth"
        m_required_action = "view"
        
        def start(self):
            pass
    
    disp = displayer.Displayer()
    disp.add_generic("Module Authorization")
    
    from src.modules.utilities import get_home_endpoint
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("Authorization Showcase", "demo_auth.index", [])
    disp.add_breadcrumb("Module Demo", "demo_auth.module_demo", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    
    code = '''class ProtectedAction(Action):
    m_default_name = "Protected Module"
    m_required_permission = "Demo_Auth"
    m_required_action = "view"

disp.add_module(ProtectedAction)  # Auto-checks permission'''
    disp.add_display_item(displayer.DisplayerItemCode("code_module_demo", code, language="python"), 0)
    
    # Add the module - it auto-checks permissions
    disp.add_module(ProtectedAction)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_back", "Back", icon="arrow-left",
        link=url_for('demo_auth.index'),
        color=displayer.BSstyle.SECONDARY
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


# Export blueprint
bp = demo_auth_bp
