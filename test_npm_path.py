import os
import subprocess

# Check if npm directory is in PATH
npm_dir = r"C:\Users\J\AppData\Roaming\npm"
path = os.environ.get('PATH', '')

print(f"Checking for: {npm_dir}")
print(f"In Windows PATH: {npm_dir in path}")
print()

# Try to run claude.cmd
try:
    result = subprocess.run(
        [r"C:\Users\J\AppData\Roaming\npm\claude.cmd", "--version"],
        capture_output=True,
        text=True,
        shell=True
    )
    print(f"Direct path works: {result.returncode == 0}")
    print(f"Output: {result.stdout}")
except Exception as e:
    print(f"Error: {e}")
