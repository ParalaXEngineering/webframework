"""
Demo Threaded Action for Scheduler Testing

This module demonstrates how the scheduler works with threaded actions,
showing all the different message types and features.
"""

from src.modules.threaded import Threaded_action
from src.modules import scheduler
import time
import random


class DemoSchedulerAction(Threaded_action):
    """Demo action that showcases all scheduler functionality."""
    
    m_default_name = "Scheduler Demo"
    
    def __init__(self):
        super().__init__()
        self.demo_type = "simple"  # simple, complex, error, multi_step
        
    def set_demo_type(self, demo_type: str):
        """Set the type of demo to run."""
        self.demo_type = demo_type
    
    def action(self):
        """Main action that demonstrates scheduler features."""
        
        if self.demo_type == "simple":
            self._demo_simple_progress()
        elif self.demo_type == "complex":
            self._demo_complex_operations()
        elif self.demo_type == "error":
            self._demo_error_handling()
        elif self.demo_type == "multi_step":
            self._demo_multi_step()
        elif self.demo_type == "all_features":
            self._demo_all_features()
        
        self.delete()
    
    def _demo_simple_progress(self):
        """Simple progress bar demo."""
        self.m_scheduler.emit_popup(
            scheduler.logLevel.info,
            "Starting simple progress demo..."
        )
        
        # Simulate work with progress updates - using status_id to update the same line
        for i in range(0, 101, 10):
            self.m_scheduler.emit_status(
                self.get_name(),
                f"Processing step {i//10 + 1} of 11",
                i,
                "",
                status_id="simple_progress"  # This keeps updating the same line!
            )
            time.sleep(0.5)
        
        self.m_scheduler.emit_popup(
            scheduler.logLevel.success,
            "Simple demo completed successfully!"
        )
        
        self.m_scheduler.emit_result(
            "success",
            "<strong>Result:</strong> All steps completed in 5.5 seconds"
        )
    
    def _demo_complex_operations(self):
        """Button control demo: disable, enable, and update button."""
        self.m_scheduler.emit_popup(
            scheduler.logLevel.info,
            "Demo: Button Control - Watch the 'Button Control' button!"
        )
        
        # Feature 1: Disable button
        self.m_scheduler.emit_status(
            self.get_name(),
            "Disabling button...",
            20,
            "Button will be disabled",
            status_id="button_demo"
        )
        self.m_scheduler.disable_button("demo_action_btn")
        time.sleep(2)
        
        # Feature 2: Update button content
        self.m_scheduler.emit_status(
            self.get_name(),
            "Updating button style...",
            50,
            "Button changes color",
            status_id="button_demo"
        )
        self.m_scheduler.emit_button(
            "demo_action_btn",
            "Button Updated!",
            "btn btn-warning"
        )
        time.sleep(2)
        
        # Feature 3: Enable button
        self.m_scheduler.emit_status(
            self.get_name(),
            "Re-enabling button...",
            80,
            "Button restored",
            status_id="button_demo"
        )
        self.m_scheduler.enable_button("demo_action_btn")
        time.sleep(1)
        
        # Restore original button
        self.m_scheduler.emit_button(
            "demo_action_btn",
            "Button Control",
            "btn btn-primary"
        )
        
        self.m_scheduler.emit_status(
            self.get_name(),
            "Button control demo complete",
            100,
            "All button features shown",
            status_id="button_demo"
        )
        
        self.m_scheduler.emit_popup(
            scheduler.logLevel.success,
            "Button control demo completed!"
        )
        
        self.m_scheduler.emit_result(
            "success",
            "<strong>Features shown:</strong> disable_button(), enable_button(), emit_button()"
        )
    
    def _demo_error_handling(self):
        """Popup demo: shows all 4 popup types."""
        self.m_scheduler.emit_popup(
            scheduler.logLevel.info,
            "Demo: Popup Messages - Watch for 4 different popup types!"
        )
        
        # Popup 1: Success
        self.m_scheduler.emit_status(
            self.get_name(),
            "Showing SUCCESS popup...",
            25,
            "Type 1 of 4",
            status_id="popup_demo"
        )
        time.sleep(0.5)
        self.m_scheduler.emit_popup(
            scheduler.logLevel.success,
            "<strong>SUCCESS!</strong><br>This is a success message popup."
        )
        time.sleep(1.5)
        
        # Popup 2: Info
        self.m_scheduler.emit_status(
            self.get_name(),
            "Showing INFO popup...",
            50,
            "Type 2 of 4",
            status_id="popup_demo"
        )
        time.sleep(0.5)
        self.m_scheduler.emit_popup(
            scheduler.logLevel.info,
            "<strong>INFO:</strong><br>This is an informational popup."
        )
        time.sleep(1.5)
        
        # Popup 3: Warning
        self.m_scheduler.emit_status(
            self.get_name(),
            "Showing WARNING popup...",
            75,
            "Type 3 of 4",
            status_id="popup_demo"
        )
        time.sleep(0.5)
        self.m_scheduler.emit_popup(
            scheduler.logLevel.warning,
            "<strong>WARNING!</strong><br>This is a warning popup."
        )
        time.sleep(1.5)
        
        # Popup 4: Error
        self.m_scheduler.emit_status(
            self.get_name(),
            "Showing ERROR popup...",
            100,
            "Type 4 of 4",
            status_id="popup_demo"
        )
        time.sleep(0.5)
        self.m_scheduler.emit_popup(
            scheduler.logLevel.error,
            "<strong>ERROR!</strong><br>This is an error popup (just a demo, nothing's wrong!)."
        )
        time.sleep(1)
        
        self.m_scheduler.emit_result(
            "info",
            "<strong>All 4 popup types shown:</strong> Success, Info, Warning, Error"
        )
        
        self.m_scheduler.emit_popup(
            scheduler.logLevel.error,
            "<strong>Error:</strong> Simulated error for demonstration purposes."
        )
        
        self.m_scheduler.emit_result(
            "danger",
            "<strong>Error Details:</strong> This is a simulated error to show how the scheduler handles failures."
        )
        
        time.sleep(1)
    
    def _demo_multi_step(self):
        """Multi-step process demonstrating MULTIPLE status lines (different IDs)."""
        self.m_scheduler.emit_popup(
            scheduler.logLevel.info,
            "Starting multi-step process - watch multiple progress bars!"
        )
        
        # Demo: Multiple concurrent status lines with DIFFERENT IDs
        phases = [
            ("phase1", "Phase 1: Data Collection", 5),
            ("phase2", "Phase 2: Data Processing", 5),
            ("phase3", "Phase 3: Report Generation", 5)
        ]
        
        for phase_id, phase_name, steps in phases:
            for step in range(1, steps + 1):
                progress = int((step / steps) * 100)
                self.m_scheduler.emit_status(
                    self.get_name(),
                    f"{phase_name} - Step {step}/{steps}",
                    progress,
                    f"{progress}% complete",
                    status_id=phase_id  # Each phase has its own line!
                )
                time.sleep(0.4)
        
        self.m_scheduler.emit_popup(
            scheduler.logLevel.success,
            "Multi-step process completed! Notice how each phase had its own progress bar."
        )
        
        self.m_scheduler.emit_result(
            "success",
            "<strong>Completed:</strong> 3 parallel phases tracked independently"
        )
    
    def _demo_all_features(self):
        """Content reload demo: dynamically updates page content without refresh."""
        self.m_scheduler.emit_popup(
            scheduler.logLevel.info,
            "Demo: Content Reload - Watch the 'Dynamic Content Area' box below!"
        )
        
        # Update 1
        self.m_scheduler.emit_status(
            self.get_name(),
            "Preparing first update...",
            20,
            "Loading content",
            status_id="reload_demo"
        )
        time.sleep(1)
        
        current_time = time.strftime("%H:%M:%S")
        reloader = [{
            'id': 'dynamic_content_demo',
            'content': f'''
            <div class="alert alert-info">
                <h5>First Update!</h5>
                <p>Content was <strong>dynamically reloaded</strong> at <code>{current_time}</code></p>
                <p class="mb-0">Watch for more updates...</p>
            </div>
            '''
        }]
        self.m_scheduler.emit_reload(reloader)
        time.sleep(2)
        
        # Update 2
        self.m_scheduler.emit_status(
            self.get_name(),
            "Loading second update...",
            50,
            "Refreshing content",
            status_id="reload_demo"
        )
        time.sleep(1)
        
        current_time = time.strftime("%H:%M:%S")
        reloader = [{
            'id': 'dynamic_content_demo',
            'content': f'''
            <div class="alert alert-warning">
                <h5>Second Update!</h5>
                <p>Content updated again at <code>{current_time}</code></p>
                <p class="mb-0">Notice how the page doesn't refresh - just the content!</p>
            </div>
            '''
        }]
        self.m_scheduler.emit_reload(reloader)
        time.sleep(2)
        
        # Final update
        self.m_scheduler.emit_status(
            self.get_name(),
            "Final update...",
            80,
            "Completing demo",
            status_id="reload_demo"
        )
        time.sleep(1)
        
        current_time = time.strftime("%H:%M:%S")
        reloader = [{
            'id': 'dynamic_content_demo',
            'content': f'''
            <div class="alert alert-success">
                <h5>Final Update - Demo Complete!</h5>
                <p>Last update at <code>{current_time}</code></p>
                <p><strong>Key Points:</strong></p>
                <ul>
                    <li>No page refresh needed</li>
                    <li>Updates any element by ID</li>
                    <li>Can update multiple elements at once</li>
                    <li>Perfect for real-time dashboards</li>
                </ul>
                <p class="mb-0">This is powered by <code>emit_reload()</code></p>
            </div>
            '''
        }]
        self.m_scheduler.emit_reload(reloader)
        
        self.m_scheduler.emit_status(
            self.get_name(),
            "Content reload demo complete!",
            100,
            "All updates shown",
            status_id="reload_demo"
        )
        
        self.m_scheduler.emit_popup(
            scheduler.logLevel.success,
            "Content Reload Demo Complete! The box was updated 3 times without page refresh."
        )
        
        self.m_scheduler.emit_result(
            "success",
            "<strong>Feature shown:</strong> emit_reload() - dynamically updates page content"
        )
