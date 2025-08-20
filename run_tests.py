#!/usr/bin/env python3
"""
Test runner for Tellescope Canvas SDK

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py protocols         # Run protocol tests only
    python run_tests.py utilities         # Run utility tests only
    python run_tests.py -v                # Run with verbose output
"""

import sys
import subprocess
import argparse


def run_tests(test_type=None, verbose=False):
    """Run tests using pytest"""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if test_type == "protocols":
        cmd.append("tests/test_protocols/")
    elif test_type == "utilities":
        cmd.append("tests/test_utilities/")
    else:
        cmd.append("tests/")
    
    return subprocess.run(cmd)


def main():
    parser = argparse.ArgumentParser(description="Run Tellescope Canvas SDK tests")
    parser.add_argument("test_type", nargs="?", choices=["protocols", "utilities"],
                       help="Type of tests to run (default: all)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Run tests with verbose output")
    
    args = parser.parse_args()
    
    result = run_tests(args.test_type, args.verbose)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()