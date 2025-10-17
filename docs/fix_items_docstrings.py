#!/usr/bin/env python3
"""
Automated fix for displayer/items.py docstrings.
Adds Returns documentation to instantiate_test methods and Args to display/setText methods.
"""

import re
from pathlib import Path

# Path to the file
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == 'docs' else SCRIPT_DIR
ITEMS_FILE = PROJECT_ROOT / 'src' / 'modules' / 'displayer' / 'items.py'

def fix_instantiate_test_docstrings(content: str) -> str:
    """Add Returns documentation to instantiate_test methods."""
    
    # Pattern to match instantiate_test methods with docstrings that don't have Returns
    pattern = r'(@classmethod\s+def instantiate_test\(cls\):\s+"""[^"]+""")'
    
    def replacer(match):
        docstring_block = match.group(1)
        
        # Skip if already has Returns
        if 'Returns:' in docstring_block:
            return docstring_block
        
        # Extract the docstring text
        parts = docstring_block.split('"""')
        if len(parts) >= 3:
            before_doc = parts[0] + '"""'
            doc_text = parts[1].strip()
            after_doc = '"""' + parts[2] if len(parts) > 2 else '"""'
            
            # Add Returns section
            new_doc = f'{before_doc}{doc_text}\n        \n        Returns:\n            Instance of the class with test data.\n        {after_doc}'
            return new_doc
        
        return docstring_block
    
    return re.sub(pattern, replacer, content, flags=re.DOTALL)

def fix_setText_methods(content: str) -> str:
    """Add Args documentation to setText methods."""
    
    # Pattern for setText without Args
    pattern = r'(def setText\(self, text\):\s+"""[^"]+""")'
    
    def replacer(match):
        docstring_block = match.group(1)
        
        # Skip if already has Args
        if 'Args:' in docstring_block or 'text:' in docstring_block.lower():
            return docstring_block
        
        # Extract parts
        parts = docstring_block.split('"""')
        if len(parts) >= 3:
            before_doc = parts[0] + '"""'
            doc_text = parts[1].strip()
            after_doc = '"""' + parts[2] if len(parts) > 2 else '"""'
            
            # Add Args section
            new_doc = f'{before_doc}{doc_text}\n        \n        Args:\n            text: The new text content to set.\n        {after_doc}'
            return new_doc
        
        return docstring_block
    
    return re.sub(pattern, replacer, content, flags=re.DOTALL)

def fix_display_methods(content: str) -> str:
    """Add Args documentation to display methods missing container/parent_id."""
    
    # Pattern for display methods with container and parent_id
    pattern = r'(def display\(self, container[^)]*parent_id[^)]*\):\s+"""[^"]*?""")'
    
    def replacer(match):
        docstring_block = match.group(1)
        
        # Skip if already documents container and parent_id
        if 'container:' in docstring_block.lower() and 'parent_id:' in docstring_block.lower():
            return docstring_block
        
        # Skip if already has Args section with both
        doc_lower = docstring_block.lower()
        if 'args:' in doc_lower and 'container' in doc_lower and 'parent_id' in doc_lower:
            return docstring_block
        
        # Extract parts
        parts = docstring_block.split('"""')
        if len(parts) >= 3:
            before_doc = parts[0] + '"""'
            doc_text = parts[1].strip()
            after_doc = '"""' + parts[2] if len(parts) > 2 else '"""'
            
            # Check if Args section exists
            if 'Args:' in doc_text:
                # Add to existing Args
                lines = doc_text.split('\n')
                new_lines = []
                args_found = False
                for line in lines:
                    new_lines.append(line)
                    if 'Args:' in line:
                        args_found = True
                        # Add the two args right after Args:
                        indent = '            '
                        new_lines.append(f'{indent}container: The container element to display in.')
                        new_lines.append(f'{indent}parent_id: The parent element ID.')
                new_doc = f'{before_doc}{chr(10).join(new_lines)}\n        {after_doc}'
            else:
                # Create new Args section
                new_doc = f'{before_doc}{doc_text}\n        \n        Args:\n            container: The container element to display in.\n            parent_id: The parent element ID.\n        {after_doc}'
            return new_doc
        
        return docstring_block
    
    return re.sub(pattern, replacer, content, flags=re.DOTALL)

def fix_get_required_resources(content: str) -> str:
    """Add Returns documentation to get_required_resources methods."""
    
    pattern = r'(def get_required_resources\(self\):\s+"""[^"]+""")'
    
    def replacer(match):
        docstring_block = match.group(1)
        
        # Skip if already has Returns
        if 'Returns:' in docstring_block:
            return docstring_block
        
        # Extract parts
        parts = docstring_block.split('"""')
        if len(parts) >= 3:
            before_doc = parts[0] + '"""'
            doc_text = parts[1].strip()
            after_doc = '"""' + parts[2] if len(parts) > 2 else '"""'
            
            # Add Returns section
            new_doc = f'{before_doc}{doc_text}\n        \n        Returns:\n            List of required resource paths.\n        {after_doc}'
            return new_doc
        
        return docstring_block
    
    return re.sub(pattern, replacer, content, flags=re.DOTALL)

def main():
    """Main function to fix all docstring issues in items.py."""
    
    print(f"Reading {ITEMS_FILE}...")
    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    print("Fixing instantiate_test methods...")
    content = fix_instantiate_test_docstrings(content)
    
    print("Fixing setText methods...")
    content = fix_setText_methods(content)
    
    print("Fixing display methods...")
    content = fix_display_methods(content)
    
    print("Fixing get_required_resources methods...")
    content = fix_get_required_resources(content)
    
    if content != original_content:
        print(f"\nWriting changes to {ITEMS_FILE}...")
        with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ File updated successfully!")
    else:
        print("ℹ️  No changes needed.")
    
    return 0

if __name__ == '__main__':
    exit(main())
