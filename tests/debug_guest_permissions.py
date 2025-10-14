#!/usr/bin/env python3
"""
Debug script to check GUEST user permissions.
"""
import sys
sys.path.insert(0, '/Users/mremacle/Documents/ParalaX/dev.nosync/webframework/src')

from modules.auth.auth_manager import auth_manager

def main():
    print("=" * 60)
    print("GUEST USER PERMISSIONS DEBUG")
    print("=" * 60)
    
    username = "GUEST"
    modules = ["Demo_Threading", "Demo_Scheduler", "Demo_Auth"]
    actions = ["view", "read", "write", "execute"]
    
    # Check if user exists
    user = auth_manager._users.get(username)
    if not user:
        print(f"❌ User '{username}' not found!")
        return
    
    print(f"\n✓ User found: {username}")
    print(f"  Groups: {user.groups}")
    print(f"  Is readonly: {user.is_readonly}")
    
    # Check permissions for each module
    for module in modules:
        print(f"\n--- Module: {module} ---")
        
        # Check if module permission exists
        module_perm = auth_manager._permissions.get(module)
        if not module_perm:
            print(f"  ⚠️  Module permission not defined")
            continue
        
        print(f"  ✓ Module permission defined")
        print(f"    Groups with access: {list(module_perm.groups.keys())}")
        
        # Check each action
        for action in actions:
            has_perm = auth_manager.has_permission(username, module, action)
            status = "✓" if has_perm else "✗"
            print(f"    {status} {action}: {has_perm}")
            
            # Show which groups have this action
            for group in user.groups:
                allowed_actions = module_perm.groups.get(group, [])
                if action in allowed_actions:
                    print(f"       └─ {group} grants this action")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
