"""
Demo Threaded Action for Scheduler Testing

This module demonstrates how the scheduler works with threaded actions,
showing all the different message types and features.
"""

from src.modules.threaded import Threaded_action
from src.modules import scheduler
import time


class DemoSchedulerAction(Threaded_action):
    """Demo action that showcases all scheduler functionality."""
    
    m_default_name = "Scheduler Demo"
    m_required_permission = "Demo_Scheduler"
    m_required_action = "view"
    
    def __init__(self):
        super().__init__()
        self.demo_type = "simple"  # simple, complex, error, multi_step
        
    def set_demo_type(self, demo_type: str):
        """Set the type of demo to run."""
        self.demo_type = demo_type
    
    def action(self):
        """Main action that demonstrates scheduler features."""
        
        if self.demo_type == "single_progress":
            self._demo_single_progress()
        elif self.demo_type == "parallel_progress":
            self._demo_parallel_progress()
        elif self.demo_type == "popup_demo":
            self._demo_popup()
        elif self.demo_type == "alert_progress":
            self._demo_alert_progress()
        elif self.demo_type == "button_control":
            self._demo_button_control()
        elif self.demo_type == "dynamic_content":
            self._demo_dynamic_content()
        elif self.demo_type == "all_features":
            self._demo_all_features()
        else:
            # Default to simple if unknown
            self._demo_single_progress()
        
        self.delete()
    
    def _demo_single_progress(self):
        """Simple progress bar demo."""
        # Simulate work with progress updates
        for i in range(0, 101, 10):
            self.m_scheduler.emit_status(
                self.get_name(),
                f"Processing {i//10 + 1}/11",
                i,
                f"{i}%",
                status_id="single_progress"
            )
            time.sleep(0.5)
        
        self.m_scheduler.emit_popup(
            scheduler.logLevel.success,
            "Single progress completed!"
        )
    
    def _demo_parallel_progress(self):
        """Multiple concurrent progress bars."""
        # Create 3 parallel progress bars
        tasks = [
            ("task1", "Task 1: Data Collection", 5),
            ("task2", "Task 2: Data Processing", 7),
            ("task3", "Task 3: Report Generation", 6)
        ]
        
        max_steps = max(t[2] for t in tasks)
        
        for step in range(1, max_steps + 1):
            for task_id, task_name, total_steps in tasks:
                if step <= total_steps:
                    progress = int((step / total_steps) * 100)
                    self.m_scheduler.emit_status(
                        self.get_name(),
                        f"{task_name} - Step {step}/{total_steps}",
                        progress,
                        f"{progress}%",
                        status_id=task_id
                    )
            time.sleep(0.6)
        
        self.m_scheduler.emit_popup(
            scheduler.logLevel.success,
            "All parallel tasks completed!"
        )
    
    def _demo_popup(self):
        """Shows all 4 popup types."""
        # Info popup
        self.m_scheduler.emit_popup(
            scheduler.logLevel.info,
            "Starting process..."
        )
        time.sleep(1)
        
        # Success popup
        self.m_scheduler.emit_popup(
            scheduler.logLevel.success,
            "<strong>Task completed!</strong><br>Operation was successful."
        )
        time.sleep(1)
        
        # Warning popup
        self.m_scheduler.emit_popup(
            scheduler.logLevel.warning,
            "<strong>Warning:</strong><br>Please review your settings."
        )
        time.sleep(1)
        
        # Error popup (just demo)
        self.m_scheduler.emit_popup(
            scheduler.logLevel.error,
            "<strong>Error occurred</strong><br>(Just a demo - nothing's wrong!)"
        )
    
    def _demo_alert_progress(self):
        """Shows alert popup during progress."""
        for i in range(5):
            progress = (i + 1) * 20
            self.m_scheduler.emit_status(
                self.get_name(),
                f"Step {i+1}/5",
                progress,
                f"{progress}%",
                status_id="alert_progress"
            )
            
            # Show alert at halfway point
            if i == 2:
                self.m_scheduler.emit_popup(
                    scheduler.logLevel.warning,
                    "Halfway done! Keep going..."
                )
            
            time.sleep(0.8)
        
        self.m_scheduler.emit_popup(
            scheduler.logLevel.success,
            "Progress with alerts complete!"
        )
    
    def _demo_button_control(self):
        """Button control: disable and enable dynamically."""
        # Disable the button
        self.m_scheduler.disable_button("btn_button_control")
        
        for i in range(5):
            progress = (i + 1) * 20
            self.m_scheduler.emit_status(
                self.get_name(),
                f"Working {i+1}/5 (button disabled)",
                progress,
                f"{progress}%",
                status_id="button_control"
            )
            time.sleep(0.5)
        
        # Re-enable the button
        self.m_scheduler.enable_button("btn_button_control")
        
        self.m_scheduler.emit_popup(
            scheduler.logLevel.success,
            "Button control demo complete - button re-enabled!"
        )
    
    def _demo_dynamic_content(self):
        """Updates page content dynamically without page refresh."""
        for i in range(5):
            # Update progress
            progress = (i + 1) * 20
            self.m_scheduler.emit_status(
                self.get_name(),
                f"Update {i+1}/5",
                progress,
                f"{progress}%",
                status_id="dynamic_content"
            )
            
            # Update the dynamic content area
            current_time = time.strftime("%H:%M:%S")
            alert_class = ["info", "success", "warning", "primary", "secondary"][i]
            reloader = [{
                'id': 'scheduler_demo_dynamic_content',
                'content': f'''
                <div class="alert alert-{alert_class}">
                    <h5>Update {i+1}/5</h5>
                    <p>Content updated at <code>{current_time}</code></p>
                    <p class="mb-0"><small>No page refresh needed!</small></p>
                </div>
                '''
            }]
            self.m_scheduler.emit_reload(reloader)
            time.sleep(1)
        
        self.m_scheduler.emit_popup(
            scheduler.logLevel.success,
            "Dynamic content demo complete!"
        )
    
    def _demo_all_features(self):
        """Comprehensive demo with all features combined."""
        # Disable button
        self.m_scheduler.disable_button("btn_all_features")
        
        # Show initial popup
        self.m_scheduler.emit_popup(
            scheduler.logLevel.info,
            "Starting comprehensive demo..."
        )
        time.sleep(1)
        
        # Run through all features
        for i in range(5):
            progress = (i + 1) * 20
            
            # Update progress
            self.m_scheduler.emit_status(
                self.get_name(),
                f"Step {i+1}/5 - All features in action",
                progress,
                f"{progress}%",
                status_id="all_features"
            )
            
            # Update dynamic content
            current_time = time.strftime("%H:%M:%S")
            reloader = [{
                'id': 'scheduler_demo_dynamic_content',
                'content': f'''
                <div class="alert alert-primary">
                    <h5>Step {i+1}/5</h5>
                    <p>Progress: <strong>{progress}%</strong></p>
                    <p>Time: <code>{current_time}</code></p>
                    <div class="progress">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             style="width: {progress}%">{progress}%</div>
                    </div>
                </div>
                '''
            }]
            self.m_scheduler.emit_reload(reloader)
            
            # Show popup at midpoint
            if i == 2:
                self.m_scheduler.emit_popup(
                    scheduler.logLevel.warning,
                    "Halfway through the comprehensive demo!"
                )
            
            time.sleep(1)
        
        # Re-enable button
        self.m_scheduler.enable_button("btn_all_features")
        
        # Final popup
        self.m_scheduler.emit_popup(
            scheduler.logLevel.success,
            "<strong>All Features Demo Complete!</strong><br>Progress, popup, button control, and dynamic content all working together."
        )
