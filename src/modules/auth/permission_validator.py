"""
Permission System Startup Validation

This module validates permission configuration at startup and warns about common issues.
"""

from typing import List, Tuple
from modules.auth.permission_registry import permission_registry
from modules.auth.auth_manager import auth_manager
from modules.log.logger_factory import get_logger

logger = get_logger("permission_validator")


def validate_permissions() -> List[Tuple[str, str]]:
    """
    Validate permission configuration at startup.
    
    Returns:
        List of (severity, message) tuples where severity is 'WARNING', 'ERROR', or 'INFO'
    """
    issues = []
    
    if not auth_manager:
        issues.append(("INFO", "Authentication system not enabled - skipping permission validation"))
        return issues
    
    # Get all registered modules
    registered_modules = permission_registry.get_all_modules()
    
    if not registered_modules:
        issues.append(("WARNING", "No modules registered with permission_registry - this may be intentional"))
        return issues
    
    logger.info(f"Validating permissions for {len(registered_modules)} registered modules...")
    
    # Check each registered module
    for module_name in registered_modules:
        # Get actions from registry
        registered_actions = set(permission_registry.get_module_actions(module_name))
        
        # Get permissions from auth_manager
        module_perms = auth_manager.get_module_permissions(module_name)
        
        if not module_perms:
            issues.append((
                "ERROR",
                f"Module '{module_name}' registered but has NO permissions configured! "
                f"Add it to permissions.json with appropriate group permissions."
            ))
            continue
        
        # Check for old CRUD action names
        old_actions = {"read", "write"} & registered_actions
        if old_actions:
            issues.append((
                "WARNING",
                f"Module '{module_name}' uses old CRUD action names: {old_actions}. "
                f"Consider using 'view' (implicit) instead."
            ))
        
        # Check if guest group exists and has permissions
        if "guest" in module_perms:
            guest_actions = module_perms["guest"]
            if not guest_actions:
                issues.append((
                    "INFO",
                    f"Module '{module_name}': guest group has no permissions (explicitly denied)"
                ))
        
        # Validate that actions in permissions match registered actions
        for group, actions in module_perms.items():
            invalid_actions = set(actions) - registered_actions
            if invalid_actions:
                issues.append((
                    "WARNING",
                    f"Module '{module_name}', group '{group}' has unregistered actions: {invalid_actions}. "
                    f"These may be from old configuration. Registered actions: {registered_actions}"
                ))
    
    # Summary
    errors = sum(1 for sev, _ in issues if sev == "ERROR")
    warnings = sum(1 for sev, _ in issues if sev == "WARNING")
    
    if errors == 0 and warnings == 0:
        issues.append(("INFO", f"✓ Permission validation passed for all {len(registered_modules)} modules"))
    else:
        issues.append((
            "INFO",
            f"Permission validation complete: {errors} errors, {warnings} warnings, {len(registered_modules)} modules checked"
        ))
    
    return issues


def log_validation_results(issues: List[Tuple[str, str]]):
    """Log validation results with appropriate severity."""
    for severity, message in issues:
        if severity == "ERROR":
            logger.error(f"PERMISSION ERROR: {message}")
        elif severity == "WARNING":
            logger.warning(f"PERMISSION WARNING: {message}")
        else:
            logger.info(message)


def validate_and_log():
    """Run validation and log results. Call this at application startup."""
    logger.info("=" * 70)
    logger.info("Starting Permission System Validation")
    logger.info("=" * 70)
    
    issues = validate_permissions()
    log_validation_results(issues)
    
    # Print critical errors to console
    errors = [msg for sev, msg in issues if sev == "ERROR"]
    if errors:
        print("\n" + "!" * 70)
        print("CRITICAL PERMISSION ERRORS DETECTED:")
        print("!" * 70)
        for error in errors:
            print(f"  ✗ {error}")
        print("\nPlease fix these issues before proceeding to production!")
        print("See logs for full details.")
        print("!" * 70 + "\n")
    
    logger.info("=" * 70)
    logger.info("Permission Validation Complete")
    logger.info("=" * 70)
