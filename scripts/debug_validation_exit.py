#!/usr/bin/env python3
"""
Debug script to identify why validate-gcp-setup.sh exits silently after Prerequisites.
Created: 2025-11-13
Purpose: Reproduce the exact failure conditions and trace the exit point
"""
import subprocess
import sys
import os

def run_bash_test(script_content: str, description: str) -> tuple[int, str, str]:
    """Run a bash script and capture output, error, and exit code."""
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"{'='*70}")

    result = subprocess.run(
        ['bash', '-c', script_content],
        capture_output=True,
        text=True
    )

    print(f"Exit Code: {result.returncode}")
    print(f"\nSTDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"\nSTDERR:\n{result.stderr}")

    return result.returncode, result.stdout, result.stderr


# Test 1: Check if arithmetic expansion exits with set -e
test1 = r"""
set -euo pipefail
PASSED=0
echo "Before increment: PASSED=$PASSED"
((PASSED++))
echo "After increment: PASSED=$PASSED"
echo "Script continues normally"
"""
run_bash_test(test1, "Arithmetic expansion with set -euo pipefail")


# Test 2: Check if PASSED++ on an uninitialized variable causes issues
test2 = r"""
set -euo pipefail
# Note: PASSED is NOT initialized
echo "Before increment"
((PASSED++))
echo "After increment"
"""
run_bash_test(test2, "Increment uninitialized variable (edge case)")


# Test 3: Simulate the exact function structure from the script
test3 = r"""
set -euo pipefail

PASSED=0
log_success() {
  echo -e "✓ $*"
  ((PASSED++))
}

check_command() {
  if ! command -v "$1" &> /dev/null; then
    echo "✗ Required command '$1' not found"
    exit 2
  fi
}

echo "=== Prerequisites ==="
check_command bash
log_success "All required commands are available"
echo "Script continues to next section"
"""
run_bash_test(test3, "Exact function structure from script")


# Test 4: Test with functions defined in different order
test4 = r"""
set -euo pipefail

PASSED=0

check_command() {
  if ! command -v "$1" &> /dev/null; then
    echo "✗ Required command '$1' not found"
    exit 2
  fi
}

log_success() {
  echo -e "✓ $*"
  ((PASSED++))
}

echo "=== Prerequisites ==="
check_command bash
log_success "All required commands are available"
echo "Script continues"
"""
run_bash_test(test4, "Functions defined in reverse order")


# Test 5: Check if echo -e with color codes causes issues
test5 = r"""
set -euo pipefail

PASSED=0
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_success() {
  echo -e "${GREEN}✓${NC} $*"
  ((PASSED++))
}

echo "=== Prerequisites ==="
log_success "All required commands are available"
echo "Script continues"
"""
run_bash_test(test5, "echo -e with ANSI color codes")


# Test 6: Test incrementing counter inside function multiple times
test6 = r"""
set -euo pipefail

PASSED=0

log_success() {
  echo -e "✓ $*"
  ((PASSED++))
}

check_command() {
  if ! command -v "$1" &> /dev/null; then
    echo "✗ Command not found: $1"
    exit 2
  fi
}

echo "=== Checking commands ==="
check_command bash
check_command echo
log_success "All required commands are available"
echo "Next section"
"""
run_bash_test(test6, "Multiple check_command calls before log_success")


# Test 7: Check actual exit code of the real script
print(f"\n{'='*70}")
print("TEST: Run actual validate-gcp-setup.sh with set -x")
print(f"{'='*70}")
result = subprocess.run(
    ['bash', '-x', '/Users/bryn/repos/selflytics/scripts/validate-gcp-setup.sh'],
    capture_output=True,
    text=True,
    timeout=10
)
print(f"Exit Code: {result.returncode}")
print(f"\nLast 50 lines of STDERR (trace):")
lines = result.stderr.split('\n')
for line in lines[-50:]:
    print(line)

print(f"\nLast 20 lines of STDOUT:")
lines = result.stdout.split('\n')
for line in lines[-20:]:
    print(line)
