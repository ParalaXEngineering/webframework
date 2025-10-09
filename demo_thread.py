"""
Demo Thread for Testing - Simple background thread to demonstrate the threading UI

Add this to demo.py to have threads show up in the /threads/ page
"""

from src.modules.threaded import Threaded_action
import time


class DemoBackgroundThread(Threaded_action):
    """Simple demo thread that runs in background"""
    
    m_default_name = "Demo Background Worker"
    m_type = "demo"
    
    def __init__(self):
        super().__init__()
        self.m_background = True  # Keep thread in manager after completion
    
    def action(self):
        """Simple counting action with console output"""
        self.console_write("=== Demo Thread Started ===", "INFO")
        self.log_write("Background worker initialized", "INFO")
        
        for i in range(100):
            # Update progress
            self.m_running_state = i
            
            # Console output every 10%
            if i % 10 == 0:
                self.console_write(f"Progress: {i}%", "INFO")
                self.log_write(f"Checkpoint at {i}%", "INFO")
            
            # Simulate work
            time.sleep(0.5)
        
        self.m_running_state = 100
        self.console_write("=== Demo Thread Completed ===", "INFO")
        self.log_write("Background worker finished", "INFO")


# ============================================================================
# TO ADD TO demo.py:
# ============================================================================
"""
# Near the end of demo.py, before app.run(), add:

# Start a demo thread for testing the threads UI
print("Starting demo background thread...")
demo_thread = DemoBackgroundThread()
demo_thread.start()
print("✓ Demo thread started - visit /threads/ to monitor")
"""
