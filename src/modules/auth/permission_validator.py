"""
Permission System Startup Validation

This module validates permission configuration at startup and warns about common issues.
"""

import logging
from typing import List, Tuple

from .permission_registry import permission_registry
from ..i18n.messages import (
    INFO_AUTH_NOT_ENABLED,
    INFO_NO_MODULES_REGISTERED_VALIDATOR,
    INFO_VALIDATING_PERMISSIONS,
    INFO_GUEST_NO_PERMISSIONS,
    INFO_VALIDATION_PASSED,
    INFO_VALIDATION_COMPLETE,
    ERROR_MODULE_NO_PERMISSIONS,
    ERROR_PERMISSION_VALIDATION,
    WARNING_OLD_CRUD_ACTIONS,
    WARNING_UNREGISTERED_ACTIONS,
    WARNING_PERMISSION_VALIDATION,
    TEXT_PERMISSION_VALIDATION_START,
    TEXT_PERMISSION_VALIDATION_COMPLETE,
    MSG_CRITICAL_PERMISSION_ERRORS,
    MSG_FIX_ISSUES_PRODUCTION,
    MSG_SEE_LOGS_DETAILS,
)

logger = logging.getLogger("permission_validator")


def validate_permissions() -> List[Tuple[str, str]]:
    """
    Validate permission configuration at startup.
    
    Returns:
        List of (severity, message) tuples where severity is 'WARNING', 'ERROR', or 'INFO'
    """
    issues = []
    
    # Import auth_manager here to avoid circular imports
    try:
        from . import auth_manager
    except ImportError:
        import auth
        auth_manager = auth.auth_manager
    
    if not auth_manager:
        issues.append(("INFO", str(INFO_AUTH_NOT_ENABLED)))
        return issues
    
    # Get all registered modules
    registered_modules = permission_registry.get_all_modules()
    
    if not registered_modules:
        issues.append(("WARNING", str(INFO_NO_MODULES_REGISTERED_VALIDATOR)))
        return issues
    
    logger.info(str(INFO_VALIDATING_PERMISSIONS), len(registered_modules))
    
    # Check each registered module
    for module_name in registered_modules:
        # Get actions from registry
        registered_actions = set(permission_registry.get_module_actions(module_name))
        
        # Get permissions from auth_manager
        module_perms = auth_manager.get_module_permissions(module_name)
        
        if not module_perms:
            issues.append((
                "ERROR",
                ERROR_MODULE_NO_PERMISSIONS.format(module_name=module_name)
            ))
            continue
        
        # Check for old CRUD action names
        old_actions = {"read", "write"} & registered_actions
        if old_actions:
            issues.append((
                "WARNING",
                WARNING_OLD_CRUD_ACTIONS.format(module_name=module_name, old_actions=old_actions)
            ))
        
        # Check if guest group exists and has permissions
        if "guest" in module_perms:
            guest_actions = module_perms["guest"]
            if not guest_actions:
                issues.append((
                    "INFO",
                    INFO_GUEST_NO_PERMISSIONS.format(module_name=module_name)
                ))
        
        # Validate that actions in permissions match registered actions
        for group, actions in module_perms.items():
            invalid_actions = set(actions) - registered_actions
            if invalid_actions:
                issues.append((
                    "WARNING",
                    WARNING_UNREGISTERED_ACTIONS.format(
                        module_name=module_name,
                        group=group,
                        invalid_actions=invalid_actions,
                        registered_actions=registered_actions
                    )
                ))
    
    # Summary
    errors = sum(1 for sev, _ in issues if sev == "ERROR")
    warnings = sum(1 for sev, _ in issues if sev == "WARNING")
    
    if errors == 0 and warnings == 0:
        issues.append(("INFO", INFO_VALIDATION_PASSED.format(count=len(registered_modules))))
    else:
        issues.append((
            "INFO",
            INFO_VALIDATION_COMPLETE.format(
                errors=errors,
                warnings=warnings,
                count=len(registered_modules)
            )
        ))
    
    return issues


def log_validation_results(issues: List[Tuple[str, str]]):
    """Log validation results with appropriate severity."""
    for severity, message in issues:
        if severity == "ERROR":
            logger.error(ERROR_PERMISSION_VALIDATION.format(message=message))
        elif severity == "WARNING":
            logger.warning(WARNING_PERMISSION_VALIDATION.format(message=message))
        else:
            logger.info(message)


def validate_and_log():
    """Run validation and log results. Call this at application startup."""
    logger.info(str(TEXT_PERMISSION_VALIDATION_START))
    
    issues = validate_permissions()
    log_validation_results(issues)
    
    # Print critical errors to console for visibility (startup errors need stderr)
    errors = [msg for sev, msg in issues if sev == "ERROR"]
    if errors:
        import sys
        logger.critical(str(MSG_CRITICAL_PERMISSION_ERRORS))
        for error in errors:
            logger.critical(f"  ✗ {error}")
            # Also output to stderr for startup visibility
            print(f"  ✗ {error}", file=sys.stderr)
        logger.critical(str(MSG_FIX_ISSUES_PRODUCTION))
        logger.critical(str(MSG_SEE_LOGS_DETAILS))
    
    logger.info(str(TEXT_PERMISSION_VALIDATION_COMPLETE))
