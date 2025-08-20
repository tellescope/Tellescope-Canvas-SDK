#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_canvas_command():
    """Check if canvas command is available."""
    returncode, _, _ = run_command("canvas --help")
    return returncode == 0


def install_plugin(plugin_path, use_existing_config=False, auto_select_all=False):
    """Install a canvas plugin from the given path."""
    plugin_path = Path(plugin_path).resolve()
    
    if not plugin_path.exists():
        print(f"Error: Plugin path '{plugin_path}' does not exist!")
        return False
    
    if not plugin_path.is_dir():
        print(f"Error: Plugin path '{plugin_path}' is not a directory!")
        return False
    
    print(f"Installing canvas plugin from: {plugin_path}")
    print("=" * 50)
    
    # Check if canvas command is available
    if not check_canvas_command():
        print("Error: 'canvas' command not found!")
        print("Please make sure Canvas is installed and available in your PATH.")
        return False
    
    # Check for CANVAS_MANIFEST.json
    manifest_path = plugin_path / "CANVAS_MANIFEST.json"
    configure_script_path = plugin_path / "configure_manifest.py"
    
    if not configure_script_path.exists():
        print(f"Error: configure_manifest.py not found in {plugin_path}")
        return False
    
    need_to_configure = False
    
    if not manifest_path.exists():
        print("No CANVAS_MANIFEST.json found.")
        need_to_configure = True
    elif not use_existing_config:
        print("CANVAS_MANIFEST.json exists but will be regenerated (use --use-existing-configuration to skip).")
        need_to_configure = True
    else:
        print("Using existing CANVAS_MANIFEST.json")
    
    # Run configuration script if needed
    if need_to_configure:
        print("\nRunning manifest configuration...")
        
        if auto_select_all:
            cmd = "python configure_manifest.py --all"
            print("Auto-selecting all protocols (--all flag specified)")
        else:
            cmd = "python configure_manifest.py"
        
        returncode, stdout, stderr = run_command(cmd, cwd=plugin_path)
        
        if returncode != 0:
            print(f"Error running configuration script:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
        
        print(stdout)
        
        # Verify manifest was created
        if not manifest_path.exists():
            print("Error: CANVAS_MANIFEST.json was not created by the configuration script!")
            return False
    
    # Install the plugin using canvas command
    print(f"\nInstalling plugin with: canvas install {plugin_path}")
    
    returncode, stdout, stderr = run_command(f"canvas install {plugin_path}")
    
    if returncode == 0:
        print("✓ Plugin installed successfully!")
        if stdout.strip():
            print(f"Output: {stdout}")
        return True
    else:
        print("✗ Plugin installation failed!")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Deploy a Canvas plugin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python canvas_deploy.py install .
  python canvas_deploy.py install /path/to/plugin --all
  python canvas_deploy.py install . --use-existing-configuration
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install a canvas plugin')
    install_parser.add_argument('path', help='Path to the plugin directory (use "." for current directory)')
    install_parser.add_argument('--use-existing-configuration', action='store_true',
                              help='Use existing CANVAS_MANIFEST.json if it exists (skip configuration)')
    install_parser.add_argument('--all', action='store_true',
                              help='Auto-select all protocols when running configuration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'install':
        success = install_plugin(
            args.path,
            use_existing_config=args.use_existing_configuration,
            auto_select_all=args.all
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()