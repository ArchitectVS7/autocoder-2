import subprocess
import shutil

print("Testing different ways to call claude...")
print()

# Test 1: which() - what Python's shutil finds
which_result = shutil.which("claude")
print(f"1. shutil.which('claude'): {which_result}")
print()

# Test 2: which() with .cmd extension
which_cmd = shutil.which("claude.cmd")
print(f"2. shutil.which('claude.cmd'): {which_cmd}")
print()

# Test 3: Try subprocess without shell
if which_cmd:
    try:
        result = subprocess.run(
            [which_cmd, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(f"3. subprocess.run with full path:")
        print(f"   Exit code: {result.returncode}")
        print(f"   Output: {result.stdout.strip()}")
    except Exception as e:
        print(f"3. subprocess.run failed: {e}")
