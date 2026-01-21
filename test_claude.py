import sys
import subprocess

# Test if Claude CLI works
result = subprocess.run(
    ["claude", "--version"],
    capture_output=True,
    text=True
)

print(f"Exit code: {result.returncode}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")
