#!/usr/bin/env python3
"""
Check docstring completeness across the framework.
Looks for functions/methods that are missing docstrings or have incomplete documentation.

This script can be run from either the project root or the docs directory.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Determine project root (go up one level if we're in docs/)
SCRIPT_DIR = Path(__file__).parent
if SCRIPT_DIR.name == 'docs':
    PROJECT_ROOT = SCRIPT_DIR.parent
else:
    PROJECT_ROOT = SCRIPT_DIR

# Path to source modules
SRC_PATH = PROJECT_ROOT / 'src' / 'modules'

class DocstringChecker(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.issues = []
        self.function_depth = 0  # Track nested function depth
        
    def visit_FunctionDef(self, node):
        # Skip nested functions (defined inside other functions)
        if self.function_depth > 0:
            self.function_depth += 1
            self.generic_visit(node)
            self.function_depth -= 1
            return
        
        # Skip private methods (start with _)
        if node.name.startswith('_') and not node.name.startswith('__'):
            self.function_depth += 1
            self.generic_visit(node)
            self.function_depth -= 1
            return
        
        self.function_depth += 1
        docstring = ast.get_docstring(node)
        
        # Check if docstring exists
        if not docstring:
            self.issues.append(f"  Line {node.lineno}: {node.name}() - NO DOCSTRING")
        else:
            # Check for Args if function has parameters (excluding self, cls)
            params = [arg.arg for arg in node.args.args if arg.arg not in ('self', 'cls')]
            
            if params:
                has_args = ':param' in docstring or 'Args:' in docstring or 'Arguments:' in docstring
                if not has_args:
                    self.issues.append(f"  Line {node.lineno}: {node.name}() - Missing Args documentation for: {', '.join(params)}")
            
            # Check for Returns if function is not __init__ and doesn't just pass
            is_init = node.name == '__init__'
            has_body = len(node.body) > 1 or (len(node.body) == 1 and not isinstance(node.body[0], ast.Pass))
            
            if not is_init and has_body and node.name not in ('__repr__', '__str__'):
                has_returns = ':return' in docstring or 'Returns:' in docstring or 'Return:' in docstring
                # Check if function actually returns something
                has_return_stmt = any(isinstance(n, ast.Return) and n.value is not None 
                                     for n in ast.walk(node))
                
                if has_return_stmt and not has_returns:
                    self.issues.append(f"  Line {node.lineno}: {node.name}() - Missing Returns documentation")
        
        self.generic_visit(node)
        self.function_depth -= 1
    
    def visit_ClassDef(self, node):
        # Check class docstring
        docstring = ast.get_docstring(node)
        if not docstring and not node.name.startswith('_'):
            self.issues.append(f"  Line {node.lineno}: class {node.name} - NO DOCSTRING")
        
        self.generic_visit(node)

def check_file(filepath: Path) -> List[str]:
    """Check a single Python file for docstring issues."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        checker = DocstringChecker(str(filepath))
        checker.visit(tree)
        
        return checker.issues
    except Exception as e:
        return [f"  ERROR parsing file: {e}"]

def main():
    """Main function to check all modules."""
    
    # Priority modules to check
    priority_files = [
        'action.py',
        'threaded/threaded_action.py',
        'threaded/threaded_manager.py',
        'auth/auth_manager.py',
        'auth/permission_registry.py',
        'displayer/displayer.py',
        'displayer/layout.py',
        'displayer/items.py',
        'scheduler/scheduler.py',
        'scheduler/message_queue.py',
        'site_conf.py',
        'utilities.py',
        'config_manager.py',
        'workflow.py',
        'socketio_manager.py',
    ]
    
    total_issues = 0
    
    print("=" * 80)
    print("DOCSTRING COMPLETENESS CHECK")
    print("=" * 80)
    print()
    
    for filepath in priority_files:
        full_path = SRC_PATH / filepath
        if not full_path.exists():
            print(f"⚠️  {filepath} - FILE NOT FOUND")
            continue
        
        issues = check_file(full_path)
        
        if issues:
            print(f"❌ {filepath}:")
            for issue in issues:
                print(issue)
            print()
            total_issues += len(issues)
        else:
            print(f"✅ {filepath} - All public functions/classes documented")
    
    print("=" * 80)
    print(f"SUMMARY: {total_issues} documentation issues found")
    print("=" * 80)
    
    return 0 if total_issues == 0 else 1

if __name__ == '__main__':
    exit(main())
