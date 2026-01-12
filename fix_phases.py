#!/usr/bin/env python3
import os
import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern: incomplete import followed by POWER_PHASES
    pattern = r'from power_system import\s*\n\s*POWER_PHASES = ({[^}]*})\s*\n\s*PowerPhase'
    
    if re.search(pattern, content):
        # Fix the import
        content = re.sub(pattern, r'from power_system import PowerPhase\n\nclass', content)
        # Add POWER_PHASES after class definition
        # This is a bit tricky, need to find the right spot
        print(f"Fixed import in {filepath}")
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

# Fix all character files
for fname in os.listdir('characters'):
    if fname.endswith('.py'):
        filepath = os.path.join('characters', fname)
        fix_file(filepath)
