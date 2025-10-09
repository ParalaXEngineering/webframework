"""Quick test to verify threading system works"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing threading imports...")

try:
    # Test new imports
    from src.modules.threaded import Threaded_action, Threaded_manager, thread_manager_obj
    print("✓ New imports work")
except Exception as e:
    print(f"✗ New imports failed: {e}")
    sys.exit(1)

try:
    # Test old imports (should show deprecation warning)
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from src.modules.threaded_action import Threaded_action as TA_old
        from src.modules.threaded_manager import Threaded_manager as TM_old
        
        if w:
            print(f"✓ Deprecation warning shown: {w[0].message}")
        else:
            print("⚠ No deprecation warning (may be suppressed)")
    print("✓ Old imports still work")
except Exception as e:
    print(f"✗ Old imports failed: {e}")
    sys.exit(1)

try:
    # Initialize manager
    import src.modules.threaded.threaded_manager as tm
    if tm.thread_manager_obj is None:
        tm.thread_manager_obj = Threaded_manager()
    print("✓ Thread manager initialized")
except Exception as e:
    print(f"✗ Manager initialization failed: {e}")
    sys.exit(1)

try:
    # Create a test thread
    class TestThread(Threaded_action):
        m_default_name = "TestThread"
        
        def action(self):
            self.console_write("Test message", "INFO")
    
    thread = TestThread()
    print(f"✓ Test thread created: {thread.get_name()}")
    
    # Check it's in the manager
    all_threads = tm.thread_manager_obj.get_all_threads()
    print(f"✓ Thread manager has {len(all_threads)} thread(s)")
    
    # Test console
    thread.console_write("Hello from console!", "INFO")
    output = thread.console_get_output()
    print(f"✓ Console has {len(output)} line(s)")
    
    # Test logging
    thread.log_write("Test log entry", "INFO")
    logs = thread.log_get_entries()
    print(f"✓ Logs have {len(logs)} entry(ies)")
    
    # Cleanup
    thread.delete()
    print("✓ Thread deleted")
    
except Exception as e:
    print(f"✗ Thread operations failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*50)
print("All tests passed! Threading system is working.")
print("="*50)
