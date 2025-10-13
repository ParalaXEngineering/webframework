"""
Quick test script to verify auth system endpoints.
Run this after starting the manual test webapp.
"""

import requests
import sys

BASE_URL = "http://localhost:5001"

def test_endpoint(url, expected_status, description):
    """Test an endpoint and report results."""
    try:
        response = requests.get(url, allow_redirects=False, timeout=2)
        status_ok = response.status_code == expected_status
        symbol = "✓" if status_ok else "✗"
        print(f"{symbol} {description}: {response.status_code} (expected {expected_status})")
        return status_ok
    except Exception as e:
        print(f"✗ {description}: ERROR - {e}")
        return False

def main():
    print("=" * 60)
    print("  Auth System Endpoint Tests")
    print("=" * 60)
    print()
    
    tests = [
        (f"{BASE_URL}/login", 200, "Login page loads"),
        (f"{BASE_URL}/user/profile", 302, "User profile (redirects when not logged in)"),
        (f"{BASE_URL}/user/preferences", 302, "User preferences (redirects when not logged in)"),
        (f"{BASE_URL}/admin/users", 302, "Admin users page (redirects when not logged in)"),
        (f"{BASE_URL}/admin/permissions", 302, "Admin permissions page (redirects when not logged in)"),
        (f"{BASE_URL}/admin/groups", 302, "Admin groups page (redirects when not logged in)"),
        (f"{BASE_URL}/", 200, "Home page loads"),
    ]
    
    passed = 0
    failed = 0
    
    for url, expected, desc in tests:
        if test_endpoint(url, expected, desc):
            passed += 1
        else:
            failed += 1
    
    print()
    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
