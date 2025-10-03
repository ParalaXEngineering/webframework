"""
Auto-discovery import tests.
Automatically tests all Python modules in src/ directory.
"""

import pytest
import os
import sys
import importlib
from pathlib import Path


# Get src directory
SRC_DIR = Path(__file__).parent.parent.parent / "src"


def discover_python_modules():
    """Discover all Python modules in src directory."""
    modules = []
    for file in SRC_DIR.glob("*.py"):
        if file.name.startswith("_"):
            continue
        if file.name in ["BTL.sh", "BTL.bat"]:  # Skip non-Python files
            continue
        module_name = file.stem
        modules.append(module_name)
    return sorted(modules)


def discover_classes_in_module(module):
    """Discover all classes defined in a module."""
    classes = []
    for name in dir(module):
        if name.startswith("_"):
            continue
        obj = getattr(module, name)
        if isinstance(obj, type):
            # Check if class is actually defined in this module (not imported)
            if hasattr(obj, '__module__') and obj.__module__.endswith(module.__name__.split('.')[-1]):
                classes.append(name)
    return sorted(classes)


class TestAutoImports:
    """Auto-discovery import tests."""
    
    @pytest.mark.parametrize("module_name", discover_python_modules())
    def test_module_imports(self, module_name):
        """Test that each Python module in src/ can be imported."""
        try:
            # Try relative import first (for when run as package)
            try:
                module = importlib.import_module(f"src.{module_name}")
            except (ImportError, ModuleNotFoundError):
                # Fallback to direct import
                sys.path.insert(0, str(SRC_DIR))
                module = importlib.import_module(module_name)
                sys.path.pop(0)
            
            assert module is not None, f"Module {module_name} imported but is None"
            
        except Exception as e:
            pytest.fail(f"Failed to import {module_name}: {type(e).__name__}: {e}")
    
    def test_core_modules_have_expected_classes(self):
        """Test that core modules have their main classes."""
        from src import displayer, access_manager, site_conf, workflow
        
        # Check displayer
        assert hasattr(displayer, 'Displayer')
        assert hasattr(displayer, 'DisplayerItem')
        assert hasattr(displayer, 'DisplayerLayout')
        assert hasattr(displayer, 'DisplayerCategory')  # New!
        
        # Check that key classes exist in core modules
        assert hasattr(access_manager, 'Access_manager')
        assert hasattr(displayer, 'Displayer')
        
        # Check site_conf
        assert hasattr(site_conf, 'Site_conf')
        
        # Check workflow
        assert hasattr(workflow, 'Workflow')
    
    def test_no_circular_imports(self):
        """Test that importing all modules doesn't cause circular import issues."""
        module_names = discover_python_modules()
        
        imported_modules = []
        for module_name in module_names:
            try:
                from src import access_manager  # Import a dependent module first
                module = importlib.import_module(f"src.{module_name}")
                imported_modules.append(module_name)
            except ImportError as e:
                if "cannot import" in str(e).lower() and "circular" in str(e).lower():
                    pytest.fail(f"Circular import detected in {module_name}: {e}")
                # Other import errors might be expected (missing dependencies)
        
        # At least core modules should import
        assert len(imported_modules) > 0, "No modules could be imported"


class TestModuleStructure:
    """Test the module structure and organization."""
    
    def test_src_directory_exists(self):
        """Test that src directory exists."""
        assert SRC_DIR.exists(), f"src directory not found at {SRC_DIR}"
        assert SRC_DIR.is_dir(), f"src is not a directory: {SRC_DIR}"
    
    def test_init_file_exists(self):
        """Test that src/__init__.py exists."""
        init_file = SRC_DIR / "__init__.py"
        assert init_file.exists(), "src/__init__.py not found"
    
    def test_core_modules_exist(self):
        """Test that core framework modules exist."""
        core_modules = [
            "displayer.py",
            "access_manager.py",
            "site_conf.py",
            "workflow.py",
            "common.py",
            "utilities.py"
        ]
        
        for module in core_modules:
            module_path = SRC_DIR / module
            assert module_path.exists(), f"Core module {module} not found"


if __name__ == "__main__":
    # Can be run standalone for quick testing
    print("Discovering modules...")
    modules = discover_python_modules()
    print(f"Found {len(modules)} modules:")
    for m in modules:
        print(f"  - {m}")
    
    print("\nRunning import tests...")
    pytest.main([__file__, "-v"])
