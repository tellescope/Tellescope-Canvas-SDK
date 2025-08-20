#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Tuple


def extract_description_from_file(file_path: str) -> str:
    """Extract description from the comment at the top of a protocol file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for description in comment blocks at the top
        lines = content.split('\n')
        description_lines = []
        in_description = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('# Description:'):
                in_description = True
                continue
            elif in_description and line.startswith('#'):
                # Remove the '# ' prefix and add to description
                desc_line = line[2:] if line.startswith('# ') else line[1:]
                if desc_line.strip():
                    description_lines.append(desc_line.strip())
            elif in_description and not line.startswith('#'):
                # End of comment block
                break
            elif line and not line.startswith('#'):
                # Found non-comment code, stop looking
                break
        
        if description_lines:
            return ' '.join(description_lines)
        
        # Fallback: look for docstring in Protocol class
        protocol_class_match = re.search(r'class Protocol\([^)]*\):\s*"""([^"]+)"""', content, re.DOTALL)
        if protocol_class_match:
            return protocol_class_match.group(1).strip().replace('\n', ' ')
        
        return "No description available"
    
    except Exception as e:
        return f"Error reading file: {str(e)}"


def discover_protocols() -> List[Tuple[str, str, str]]:
    """Discover all protocol files and extract their descriptions."""
    protocols_dir = "protocols"
    protocols = []
    
    if not os.path.exists(protocols_dir):
        print(f"Error: {protocols_dir} directory not found!")
        return protocols
    
    for filename in os.listdir(protocols_dir):
        if (filename.endswith('.py') and 
            filename not in ['__init__.py', '__example.py'] and 
            not filename.startswith('.')):
            
            file_path = os.path.join(protocols_dir, filename)
            description = extract_description_from_file(file_path)
            
            # Create class path based on filename (remove .py extension)
            module_name = filename[:-3]
            class_path = f"tellescope.protocols.{module_name}:Protocol"
            
            protocols.append((filename, class_path, description))
    
    return protocols


def load_example_manifest() -> Dict:
    """Load the example manifest from embedded JSON string."""
    example_manifest_json = """{
    "sdk_version": "0.1.4",
    "plugin_version": "0.0.1",
    "name": "tellescope",
    "description": "Edit the description in CANVAS_MANIFEST.json",
    "components": {
        "protocols": [
            {
                "class": "tellescope.protocols.__example.py:Protocol",
                "description": "A protocol that does xyz..."
            }
        ],
        "commands": [],
        "content": [],
        "effects": [],
        "views": []
    },
    "secrets": [],
    "tags": {},
    "references": [],
    "license": "",
    "diagram": false,
    "readme": "./README.md"
}"""
    try:
        return json.loads(example_manifest_json)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in embedded manifest: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Canvas Manifest Configuration Tool")
    parser.add_argument('--all', action='store_true', help='Include all available protocols without user interaction')
    args = parser.parse_args()
    
    print("Canvas Manifest Configuration Tool")
    print("=" * 40)
    print()
    
    # Load the example manifest
    manifest = load_example_manifest()
    
    # Discover available protocols
    protocols = discover_protocols()
    
    if not protocols:
        print("No protocol files found in the protocols directory.")
        print("Make sure you have created protocol files before running this script.")
        sys.exit(1)
    
    print(f"Found {len(protocols)} available protocol(s):")
    print()
    
    # Display available protocols
    for i, (filename, class_path, description) in enumerate(protocols, 1):
        print(f"{i}. {filename}")
        print(f"   Class: {class_path}")
        print(f"   Description: {description}")
        print()
    
    selected_protocols = []
    
    if args.all:
        # Auto-select all protocols
        selected_protocols = protocols
        print("Auto-selecting all protocols (--all flag specified)")
    else:
        # Get user selection
        print("Select the protocols you want to include in your manifest:")
        print("Enter the numbers separated by commas (e.g., 1,3,4) or 'all' for all protocols:")
        print("Press Enter without typing anything to include no protocols.")
        
        try:
            user_input = input("> ").strip()
            
            if user_input.lower() == 'all':
                selected_protocols = protocols
            elif user_input:
                # Parse comma-separated numbers
                try:
                    indices = [int(x.strip()) for x in user_input.split(',')]
                    for idx in indices:
                        if 1 <= idx <= len(protocols):
                            selected_protocols.append(protocols[idx - 1])
                        else:
                            print(f"Warning: Invalid selection '{idx}' ignored (must be between 1 and {len(protocols)})")
                except ValueError:
                    print("Error: Invalid input format. Please enter numbers separated by commas.")
                    sys.exit(1)
        
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
            sys.exit(1)
    
    try:
        # Update manifest with selected protocols
        manifest['components']['protocols'] = []
        for filename, class_path, description in selected_protocols:
            manifest['components']['protocols'].append({
                "class": class_path,
                "description": description
            })
        
        # Write the new manifest
        with open('CANVAS_MANIFEST.json', 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=4)
        
        print()
        print(f"✓ Successfully created CANVAS_MANIFEST.json with {len(selected_protocols)} protocol(s).")
        
        if selected_protocols:
            print("Selected protocols:")
            for filename, class_path, description in selected_protocols:
                print(f"  - {filename}: {description}")
        else:
            print("No protocols were selected.")
    
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()