#!/usr/bin/env python3
"""
Standalone curl-based test script for displayer demo application.

This script starts the demo server, runs curl tests against it,
and validates the responses. It's an alternative to the pytest-based
tests that can be run independently.

Usage:
    python tests/test_with_curl.sh
    
Or make it executable and run directly:
    chmod +x tests/test_with_curl.py
    ./tests/test_with_curl.py
"""

import subprocess
import time
import sys
import signal
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}ℹ {text}{RESET}")


class DemoServerManager:
    """Manages the demo Flask server lifecycle."""
    
    def __init__(self, port=5001):
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self.process = None
        
    def start(self):
        """Start the demo server."""
        demo_path = Path(__file__).parent.parent / "demo.py"
        venv_python = Path(__file__).parent.parent / ".venv" / "bin" / "python"
        
        if not venv_python.exists():
            venv_python = Path("python")
        
        print_info(f"Starting demo server on port {self.port}...")
        self.process = subprocess.Popen(
            [str(venv_python), str(demo_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr with stdout
            text=True
        )
        
        # Wait for server to be ready
        max_retries = 30
        for i in range(max_retries):
            # Check if process died
            if self.process.poll() is not None:
                # Process exited - print output
                output = self.process.stdout.read()
                print_error(f"Server process exited: {output[:500]}")
                return False
                
            try:
                result = subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", self.base_url],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.stdout == "200":
                    print_success(f"Server started successfully on {self.base_url}")
                    return True
            except (subprocess.TimeoutExpired, Exception):
                pass
            time.sleep(0.5)
        
        print_error("Server failed to start within timeout")
        # Print what we got from server
        if self.process.poll() is None:
            print_info("Server process is still running but not responding")
        return False
    
    def stop(self):
        """Stop the demo server."""
        if self.process:
            print_info("Stopping demo server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            print_success("Server stopped")
    
    def __enter__(self):
        """Context manager entry."""
        if self.start():
            return self
        raise RuntimeError("Failed to start server")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def run_get_request(server, path, expected_in_content=None):
    """Test a GET request."""
    url = f"{server.base_url}{path}"
    print(f"Testing GET {path}...")
    
    result = subprocess.run(
        ["curl", "-s", "-w", "\\n%{http_code}", url],
        capture_output=True,
        text=True
    )
    
    lines = result.stdout.strip().split("\n")
    status_code = lines[-1]
    content = "\n".join(lines[:-1])
    
    if status_code != "200":
        print_error(f"Failed: HTTP {status_code}")
        return False
    
    if expected_in_content and expected_in_content.encode() not in content.encode():
        print_error(f"Content check failed: '{expected_in_content}' not found")
        return False
    
    print_success(f"OK (HTTP {status_code})")
    print(f"   Curl: curl {url}")
    return True


def run_post_request(server, path, form_data, check_success=True):
    """Test a POST request."""
    url = f"{server.base_url}{path}"
    print(f"Testing POST {path}...")
    
    # Build curl command with form data
    curl_cmd = ["curl", "-s", "-w", "\\n%{http_code}", "-X", "POST"]
    curl_display = f"curl -X POST"
    
    for key, value in form_data.items():
        curl_cmd.extend(["-d", f"{key}={value}"])
        curl_display += f" -d '{key}={value}'"
    
    curl_cmd.append(url)
    curl_display += f" {url}"
    
    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    
    lines = result.stdout.strip().split("\n")
    status_code = lines[-1]
    content = "\n".join(lines[:-1])
    
    if status_code != "200":
        print_error(f"Failed: HTTP {status_code}")
        return False
    
    if check_success and "500" in content:
        print_error("Server error in response")
        return False
    
    print_success(f"OK (HTTP {status_code})")
    print(f"   Curl: {curl_display}")
    return True


def main():
    """Run all tests."""
    print_header("Displayer Demo - Curl-based Tests")
    
    # Start server
    try:
        with DemoServerManager() as server:
            passed = 0
            failed = 0
            
            # Test GET requests
            print_header("Testing GET Requests")
            
            tests = [
                ("/", None),
                ("/layouts", "Layout"),
                ("/text-display", "Text"),
                ("/inputs", "Input"),
                ("/complete-showcase", "Showcase"),
            ]
            
            for path, expected in tests:
                if run_get_request(server, path, expected):
                    passed += 1
                else:
                    failed += 1
            
            # Test POST requests
            print_header("Testing POST Requests")
            
            post_tests = [
                ("Simple form", {
                    "name": "John Doe",
                    "age": "30"
                }),
                ("Nested fields", {
                    "user.name": "Jane",
                    "user.age": "25",
                    "settings.theme": "dark"
                }),
                ("List fields", {
                    "tags.list0": "python",
                    "tags.list1": "flask",
                    "tags.list2": "testing"
                }),
                ("Mixed complex", {
                    "user.name": "Alice",
                    "user.email": "alice@example.com",
                    "prefs.list0": "email",
                    "prefs.list1": "sms"
                }),
            ]
            
            for test_name, form_data in post_tests:
                print(f"\n{test_name}:")
                if run_post_request(server, "/inputs", form_data):
                    passed += 1
                else:
                    failed += 1
            
            # Summary
            print_header("Test Summary")
            print(f"Total tests: {passed + failed}")
            print_success(f"Passed: {passed}")
            if failed > 0:
                print_error(f"Failed: {failed}")
            else:
                print_success("All tests passed!")
            
            return 0 if failed == 0 else 1
            
    except KeyboardInterrupt:
        print_info("\nTests interrupted by user")
        return 130
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
