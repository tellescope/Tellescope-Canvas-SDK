#!/usr/bin/env python3

import argparse
from pathlib import Path
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, interactive=False):
    """Run a command and return the result."""
    try:
        if interactive:
            # Allow interactive input/output for configuration scripts
            result = subprocess.run(cmd, shell=True, cwd=cwd, text=True)
            return result.returncode, "", ""
        else:
            # Capture output for non-interactive commands
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
            returncode, stdout, stderr = run_command(cmd, cwd=plugin_path)
        else:
            cmd = "python configure_manifest.py"
            print("Please select the protocols you want to include...")
            returncode, stdout, stderr = run_command(cmd, cwd=plugin_path, interactive=True)
        
        if returncode != 0:
            print(f"Error running configuration script (exit code: {returncode})")
            if stdout.strip():
                print(f"STDOUT: {stdout}")
            if stderr.strip():
                print(f"STDERR: {stderr}")
            return False
        
        if stdout.strip():
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
        description="Deploy a Canvas plugin from the current directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python canvas_deploy.py                            # Install from current directory
  python canvas_deploy.py --all                      # Install from current directory, auto-select all protocols
  python canvas_deploy.py --use-existing-configuration  # Use existing manifest
  python canvas_deploy.py /path/to/plugin            # Install from specific path
  python canvas_deploy.py install /path/to/plugin    # Explicit install command (optional)
        """
    )
    
    # Add main arguments directly to the parser (for default install behavior)
    parser.add_argument('path', nargs='?', default='.', 
                       help='Path to the plugin directory (defaults to current directory)')
    parser.add_argument('--use-existing-configuration', action='store_true',
                       help='Use existing CANVAS_MANIFEST.json if it exists (skip configuration)')
    parser.add_argument('--all', action='store_true',
                       help='Auto-select all protocols when running configuration')
    
    # Keep subcommands for backward compatibility
    subparsers = parser.add_subparsers(dest='command', help='Available commands (optional)')
    
    # Install command (for backward compatibility)
    install_parser = subparsers.add_parser('install', help='Install a canvas plugin (same as default behavior)')
    install_parser.add_argument('path', nargs='?', default='.', 
                              help='Path to the plugin directory (defaults to current directory)')
    install_parser.add_argument('--use-existing-configuration', action='store_true',
                              help='Use existing CANVAS_MANIFEST.json if it exists (skip configuration)')
    install_parser.add_argument('--all', action='store_true',
                              help='Auto-select all protocols when running configuration')
    
    args = parser.parse_args()
    
    # Default to install command if no subcommand specified
    if not args.command:
        # Use main parser args for default install behavior
        success = install_plugin(
            args.path,
            use_existing_config=args.use_existing_configuration,
            auto_select_all=args.all
        )
        sys.exit(0 if success else 1)
    elif args.command == 'install':
        # Use subcommand args for explicit install command
        success = install_plugin(
            args.path,
            use_existing_config=args.use_existing_configuration,
            auto_select_all=args.all
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()