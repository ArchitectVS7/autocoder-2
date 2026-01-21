import subprocess
import sys
from pathlib import Path

print("Testing MCP server dependencies...")
print()

# Test 1: Python MCP server
print("1. Testing features MCP server (Python):")
try:
    result = subprocess.run(
        [sys.executable, "-m", "mcp_server.feature_mcp", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
        cwd=str(Path(__file__).parent)
    )
    print(f"   Exit code: {result.returncode}")
    if result.stdout:
        print(f"   Stdout: {result.stdout[:200]}")
    if result.stderr:
        print(f"   Stderr: {result.stderr[:200]}")
except Exception as e:
    print(f"   Error: {e}")
print()

# Test 2: npx (for Playwright MCP)
print("2. Testing npx (for Playwright MCP):")
try:
    result = subprocess.run(
        ["npx", "--version"],
        capture_output=True,
        text=True,
        timeout=5
    )
    print(f"   Exit code: {result.returncode}")
    print(f"   Version: {result.stdout.strip()}")
except Exception as e:
    print(f"   Error: {e}")
