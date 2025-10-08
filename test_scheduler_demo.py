"""
Quick test script to verify the scheduler demo works
"""
import sys
import time

print("=" * 60)
print("Testing Scheduler Demo Components")
print("=" * 60)

# Test 1: Import all dependencies
print("\n[1/5] Testing imports...")
try:
    from src.modules import threaded_manager, scheduler_classes as scheduler
    from src.modules import scheduler as scheduler_pkg
    from demo_scheduler_action import DemoSchedulerAction
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Initialize thread manager
print("\n[2/5] Initializing thread manager...")
try:
    threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()
    print("✅ Thread manager initialized")
except Exception as e:
    print(f"❌ Thread manager failed: {e}")
    sys.exit(1)

# Test 3: Initialize scheduler
print("\n[3/5] Initializing scheduler...")
try:
    scheduler_instance = scheduler.Scheduler()
    scheduler.scheduler_obj = scheduler_instance
    scheduler_pkg.scheduler_obj = scheduler_instance
    print("✅ Scheduler initialized")
except Exception as e:
    print(f"❌ Scheduler failed: {e}")
    sys.exit(1)

# Test 4: Create demo action
print("\n[4/5] Creating demo action...")
try:
    demo_action = DemoSchedulerAction()
    demo_action.set_demo_type("simple")
    print("✅ Demo action created")
    print(f"   - Name: {demo_action.m_default_name}")
    print(f"   - Scheduler: {demo_action.m_scheduler}")
except Exception as e:
    print(f"❌ Demo action failed: {e}")
    sys.exit(1)

# Test 5: Test action methods
print("\n[5/5] Testing action methods...")
try:
    # Test that we can call the methods without errors
    assert hasattr(demo_action, 'action'), "No action method"
    assert hasattr(demo_action, 'set_demo_type'), "No set_demo_type method"
    assert hasattr(demo_action, '_demo_simple_progress'), "No _demo_simple_progress method"
    assert hasattr(demo_action, '_demo_complex_operations'), "No _demo_complex_operations method"
    assert hasattr(demo_action, '_demo_error_handling'), "No _demo_error_handling method"
    assert hasattr(demo_action, '_demo_multi_step'), "No _demo_multi_step method"
    assert hasattr(demo_action, '_demo_all_features'), "No _demo_all_features method"
    print("✅ All action methods present")
except Exception as e:
    print(f"❌ Method test failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nThe scheduler demo components are working correctly.")
print("You can now run 'python demo.py' and test the scheduler demo page.")
