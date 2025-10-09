"""
Example: Enhanced Threading Demo

This script demonstrates the new threading capabilities:
- Console output
- Structured logging
- Process communication
- Progress tracking
"""

import time
from src.modules.threaded import Threaded_action, thread_manager_obj
from src.modules import scheduler
from src.modules.scheduler.scheduler import Scheduler


class DemoThread(Threaded_action):
    """Demo thread showcasing all new features"""
    
    m_default_name = "DemoThread"
    m_type = "demo"
    
    def action(self):
        """Main thread action"""
        
        # Console output (visible in UI Console tab)
        self.console_write("=== Demo Thread Started ===", "INFO")
        self.console_write("This is a demonstration of the new threading features", "INFO")
        
        # Structured logging (visible in UI Logs tab)
        self.log_write("Thread initialized successfully", "INFO")
        
        # Simulate work with progress
        for i in range(10):
            # Update progress
            self.m_running_state = i * 10
            
            # Console output
            self.console_write(f"Progress: {self.m_running_state}%", "INFO")
            
            # Structured log
            self.log_write(f"Completed step {i+1}/10", "INFO")
            
            # Warning example
            if i == 5:
                self.console_write("⚠ Halfway point reached", "WARNING")
                self.log_write("Midpoint checkpoint", "WARNING")
            
            time.sleep(0.5)
        
        # Complete
        self.m_running_state = 100
        self.console_write("=== Demo Thread Completed ===", "INFO")
        self.log_write("All steps completed successfully", "INFO")


class ProcessDemoThread(Threaded_action):
    """Demo thread with process execution"""
    
    m_default_name = "ProcessDemo"
    m_type = "process_demo"
    
    def action(self):
        """Execute a local process"""
        
        self.console_write("=== Process Demo Started ===", "INFO")
        
        # Execute a simple command
        import sys
        if sys.platform == "win32":
            # Windows
            self.console_write("Running Windows command...", "INFO")
            self.process_exec(["powershell", "-Command", "Get-Date"], ".", shell=True)
        else:
            # Linux/Mac
            self.console_write("Running Unix command...", "INFO")
            self.process_exec(["date"], ".")
        
        # Wait for process
        self.console_write("Waiting for process to complete...", "INFO")
        self.process_wait(timeout=10)
        
        # Process output is auto-captured to console
        self.console_write("Process completed", "INFO")
        self.log_write("Process execution successful", "INFO")


class ErrorDemoThread(Threaded_action):
    """Demo thread that handles errors"""
    
    m_default_name = "ErrorDemo"
    m_type = "error_demo"
    
    def action(self):
        """Demonstrate error handling"""
        
        self.console_write("=== Error Demo Started ===", "INFO")
        self.log_write("Testing error handling", "INFO")
        
        try:
            # Simulate some work
            self.console_write("Performing operation...", "INFO")
            time.sleep(1)
            
            # Simulate an error
            self.console_write("Simulating error condition", "WARNING")
            raise ValueError("This is a demo error")
            
        except Exception as e:
            # Error is automatically captured by thread wrapper
            # But you can also handle it explicitly
            self.console_write(f"Caught error: {e}", "ERROR")
            self.log_write(f"Error occurred: {e}", "ERROR")
            
            # Re-raise to let framework handle it
            raise


def run_demo():
    """Run the threading demo"""
    
    # Initialize scheduler (required)
    if not scheduler.scheduler_obj:
        scheduler.scheduler_obj = Scheduler()
    
    print("=" * 60)
    print("ENHANCED THREADING DEMO")
    print("=" * 60)
    print()
    print("Starting demo threads...")
    print()
    
    # Create and start threads
    thread1 = DemoThread()
    thread1.change_name("Demo-1")
    thread1.start()
    
    time.sleep(1)
    
    thread2 = ProcessDemoThread()
    thread2.start()
    
    print("✓ Threads started")
    print()
    print("To monitor threads:")
    print("  1. Start the application (python demo.py)")
    print("  2. Visit http://localhost:5000/threads/")
    print("  3. Click 'Details' on any thread")
    print("  4. See Console, Logs, and Process tabs")
    print()
    print("Press Ctrl+C to stop...")
    print()
    
    # Wait for threads
    try:
        while thread1.m_running or thread2.m_running:
            time.sleep(1)
            print(f"Thread 1: {thread1.m_running_state}% | Thread 2: Running={thread2.m_running}")
    except KeyboardInterrupt:
        print("\nStopping threads...")
        thread1.delete()
        thread2.delete()
    
    print("\n✓ Demo completed")
    print()
    print("Thread statistics:")
    stats = thread_manager_obj.get_thread_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    run_demo()
