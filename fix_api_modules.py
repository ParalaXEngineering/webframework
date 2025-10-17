#!/usr/bin/env python3
"""Add :no-index: to all automodule directives in api_modules.rst"""

with open('docs/source/api_modules.rst', 'r') as f:
    lines = f.readlines()

output = []
i = 0
while i < len(lines):
    output.append(lines[i])
    
    # Check if this is an automodule directive
    if lines[i].strip().startswith('.. automodule::'):
        # Add the next 3 lines (:members:, :undoc-members:, :show-inheritance:)
        if i + 3 < len(lines):
            output.append(lines[i + 1])  # :members:
            output.append(lines[i + 2])  # :undoc-members:
            output.append(lines[i + 3])  # :show-inheritance:
            
            # Check if :no-index: is NOT already on the next line
            if i + 4 >= len(lines) or ':no-index:' not in lines[i + 4]:
                # Add :no-index: with proper indentation
                output.append('   :no-index:\n')
            
            i += 4  # Skip the lines we just added
            continue
    
    i += 1

# Write back
with open('docs/source/api_modules.rst', 'w') as f:
    f.writelines(output)

print("Successfully added :no-index: to all automodule directives")
