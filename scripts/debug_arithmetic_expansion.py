#!/usr/bin/env python3
"""
Debug script to isolate the arithmetic expansion issue.
The issue is that ((PASSED++)) with set -e exits with error when PASSED is 0.
"""

import subprocess


def test_arithmetic(description: str, script: str) -> tuple[int, str]:
    """Test arithmetic expansion behavior."""
    print(f"\nTest: {description}")
    print("-" * 60)
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    print(f"Exit Code: {result.returncode}")
    print(f"Output: {result.stdout if result.stdout else '(empty)'}")
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result.returncode, result.stdout


# The critical test: post-increment with set -e
print("=" * 60)
print("CRITICAL: Post-increment ((VAR++)) with set -e")
print("=" * 60)

# Test 1: ((PASSED++)) where PASSED=0
test_arithmetic(
    "Post-increment when counter is 0 (((PASSED++)))",
    r"""
set -e
PASSED=0
echo "Before: PASSED=$PASSED"
((PASSED++))
echo "After: PASSED=$PASSED"
""",
)

# Test 2: ((++PASSED)) pre-increment
test_arithmetic(
    "Pre-increment when counter is 0 (((++PASSED)))",
    r"""
set -e
PASSED=0
echo "Before: PASSED=$PASSED"
((++PASSED))
echo "After: PASSED=$PASSED"
""",
)

# Test 3: PASSED=$((PASSED+1)) assignment
test_arithmetic(
    "Assignment form (PASSED=$((PASSED+1)))",
    r"""
set -e
PASSED=0
echo "Before: PASSED=$PASSED"
PASSED=$((PASSED+1))
echo "After: PASSED=$PASSED"
""",
)

# Test 4: Without set -e
test_arithmetic(
    "Post-increment without set -e (((PASSED++)))",
    r"""
PASSED=0
echo "Before: PASSED=$PASSED"
((PASSED++))
echo "After: PASSED=$PASSED"
""",
)

# Test 5: The actual failure case with -e and -u
test_arithmetic(
    "With set -euo pipefail",
    r"""
set -euo pipefail
PASSED=0
echo "Before: PASSED=$PASSED"
((PASSED++))
echo "After: PASSED=$PASSED"
""",
)

print("\n" + "=" * 60)
print("EXPLANATION")
print("=" * 60)
print("""
In bash, post-increment ((VAR++)) has a special behavior:
- The return value of ((PASSED++)) is the VALUE BEFORE increment
- When PASSED=0, the expression evaluates to 0
- With 'set -e', bash treats exit code 0 as success and non-zero as failure
- However, ((PASSED++)) returns the PRE-increment value, which is 0
- When the arithmetic expression evaluates to 0, bash exits with status 1

This is documented bash behavior:
  "An arithmetic command is evaluated using the rules of arithmetic
   evaluation. If the result is 0, the command returns an exit status
   of 1; otherwise, the exit status is 0."

The fix is to use one of these alternatives:
1. ((++PASSED))     - pre-increment (evaluates to 1)
2. PASSED=$((PASSED+1))  - assignment form
3. PASSED=$((PASSED))    - dummy assignment
4. (( PASSED++ )) || true - suppress error
""")
