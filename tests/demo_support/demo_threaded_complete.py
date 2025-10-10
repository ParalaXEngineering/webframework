"""
Complete Threaded Action Demo

Demonstrates all features of the Threaded_action class:
- Console writing (formatted and raw)
- Structured logging
- Process execution and output capture
- Progress tracking
- Error handling
"""

from src.modules.threaded import Threaded_action
import time
import subprocess
import sys


class DemoThreadedAction(Threaded_action):
    """Demo action showcasing all threading features."""
    
    m_default_name = "Demo Thread"
    
    def __init__(self, demo_type="complete"):
        """Initialize demo action.
        
        Args:
            demo_type: Type of demo to run (complete, console, logging, process)
        """
        super().__init__()
        self.demo_type = demo_type
        self.m_default_name = f"Demo: {demo_type.title()}"
    
    def action(self):
        """Execute the demo action."""
        self.console_write("🚀 Starting Demo Thread Action", level="INFO")
        self.log_write(f"Demo thread initialized - type: {self.demo_type}", "INFO")
        
        if self.demo_type == "complete":
            self._run_complete_demo()
        elif self.demo_type == "console":
            self._run_console_demo()
        elif self.demo_type == "logging":
            self._run_logging_demo()
        elif self.demo_type == "process":
            self._run_process_demo()
    
    def _run_complete_demo(self):
        """Run a complete demo of all features."""
        steps = [
            ("Initializing", 10),
            ("Processing data", 20),
            ("Executing tasks", 40),
            ("Running subprocess", 60),
            ("Finalizing", 80),
            ("Cleanup", 90),
        ]
        
        for step_name, progress in steps:
            self.console_write(f"📋 Step: {step_name}", level="INFO")
            self.log_write(f"Executing step: {step_name} (progress: {progress}%)", "INFO")
            self.m_running_state = progress
            time.sleep(1.5)
        
        # Run a subprocess
        self.console_write("🔧 Running system command...", level="INFO")
        self.log_write("Starting subprocess: python --version", "INFO")
        
        try:
            result = subprocess.run(
                [sys.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.console_write(f"✓ Command output: {result.stdout.strip()}", level="SUCCESS")
            self.log_write(f"Subprocess completed: {result.stdout.strip()} (returncode: {result.returncode})", "INFO")
        except Exception as e:
            self.console_write(f"✗ Error: {str(e)}", level="ERROR")
            self.log_write(f"Subprocess failed: {str(e)}", "ERROR")
        
        self.m_running_state = 100
        self.console_write("🎉 Demo completed successfully!", level="SUCCESS")
        self.log_write("Demo thread completed successfully", "INFO")
    
    def _run_console_demo(self):
        """Demo console writing features."""
        self.console_write("=== Console Demo Started ===", level="INFO")
        
        levels = ["INFO", "SUCCESS", "WARNING", "ERROR", "DEBUG"]
        for i, level in enumerate(levels):
            self.console_write(f"Message at {level} level", level=level)
            self.m_running_state = (i + 1) * 20
            time.sleep(0.8)
        
        self.console_write_raw("Raw message without formatting")
        self.console_write("🎨 Using emojis for visual feedback", level="SUCCESS")
        
        self.m_running_state = 100
        self.console_write("=== Console Demo Completed ===", level="SUCCESS")
    
    def _run_logging_demo(self):
        """Demo structured logging features."""
        self.console_write("📝 Logging Demo Started", level="INFO")
        
        log_types = [
            ("DEBUG", "Debug message - low-level info"),
            ("INFO", "Information message - status: running"),
            ("WARNING", "Warning message - risk: medium"),
            ("ERROR", "Error message - code: 500"),
        ]
        
        for i, (level, msg) in enumerate(log_types):
            self.log_write(msg, level)
            self.console_write(f"✓ Logged {level}: {msg}", level="INFO")
            self.m_running_state = (i + 1) * 25
            time.sleep(1)
        
        self.m_running_state = 100
        self.console_write("📝 Logging Demo Completed", level="SUCCESS")
    
    def _run_process_demo(self):
        """Demo process execution features."""
        self.console_write("⚙️ Process Demo Started", level="INFO")
        
        commands = [
            ([sys.executable, "--version"], "Python version"),
            ([sys.executable, "-c", "print('Hello from subprocess')"], "Print test"),
            ([sys.executable, "-c", "import sys; print(f'Platform: {sys.platform}')"], "Platform info"),
        ]
        
        for i, (cmd, desc) in enumerate(commands):
            self.console_write(f"▶ Running: {desc}", level="INFO")
            self.log_write(f"Executing command: {desc} - {' '.join(cmd)}", "INFO")
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    self.console_write(f"✓ {desc}: {result.stdout.strip()}", level="SUCCESS")
                    self.log_write(f"Command succeeded: {desc} - {result.stdout.strip()}", "INFO")
                else:
                    self.console_write(f"✗ {desc} failed", level="ERROR")
                    self.log_write(f"Command failed: {desc} - returncode: {result.returncode}", "ERROR")
            except Exception as e:
                self.console_write(f"✗ Exception: {str(e)}", level="ERROR")
                self.log_write(f"Command exception: {desc} - {str(e)}", "ERROR")
            
            self.m_running_state = (i + 1) * 33
            time.sleep(1)
        
        self.m_running_state = 100
        self.console_write("⚙️ Process Demo Completed", level="SUCCESS")
